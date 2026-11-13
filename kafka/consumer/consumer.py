import json
import logging
import os
import signal
import sys
import time
from typing import Any, Dict
from elasticsearch import Elasticsearch, ApiError, ConnectionError as ESConnectionError
from kafka import KafkaConsumer
from kafka.errors import KafkaError

# Configurações de logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("kafka-consumer")

# Variáveis de ambiente e configurações
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC_NAME = os.getenv("KAFKA_TOPIC_NAME", "enade-questoes")
CONSUMER_GROUP_ID = os.getenv("KAFKA_CONSUMER_GROUP_ID", "enade-es-indexer-group")
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
INDEX_NAME = os.getenv("ELASTICSEARCH_INDEX_NAME", "enade-questoes")
MAPPING_FILE_PATH = os.getenv("MAPPING_FILE_PATH", "elasticsearch/mapping.json")

# Controle de execução de parada graciosa
executando = True


def sinal_parada(signum, frame):
    global executando
    logger.info("Sinal de encerramento recebido. Parando consumidor graciosamente...")
    executando = False


signal.signal(signal.SIGINT, sinal_parada)
signal.signal(signal.SIGTERM, sinal_parada)


# Conexão e inicialização do elasticsearch 
def obter_cliente_elasticsearch(url: str, max_tentativas: int = 15, espera_seg: int = 4) -> Elasticsearch:
    logger.info(f"Conectando ao Elasticsearch em: {url}")
    for tentativa in range(1, max_tentativas + 1):
        try:
            es = Elasticsearch(url, request_timeout=15)
            if es.ping():
                info = es.info()
                logger.info(
                    f"Conexão com Elasticsearch OK! Versão do cluster: {info['version']['number']}"
                )
                return es
        except (ESConnectionError, Exception) as err:
            logger.warning(
                f"Tentativa {tentativa}/{max_tentativas} de conexão com Elasticsearch falhou: {err}. "
                f"Aguardando {espera_seg}s..."
            )
            time.sleep(espera_seg)

    logger.error("Falha crítica: Não foi possível conectar ao Elasticsearch.")
    sys.exit(1)


def inicializar_indice(es: Elasticsearch, nome_indice: str, caminho_mapping: str):
    """
    Verifica se o índice existe. Se não existir, carrega as definições do mapping e cria o índice. 
    """

    try:
        if es.indices.exists(index=nome_indice):
            logger.info(f"Índice '{nome_indice}' já existe no Elasticsearch.")
            return

        logger.info(f"Índice '{nome_indice}' não encontrado. Criando novo índice com mapping...")
        if not os.path.exists(caminho_mapping):
            logger.error(f"Arquivo de mapping não encontrado em: {caminho_mapping}")
            sys.exit(1)

        with open(caminho_mapping, "r", encoding="utf-8") as f:
            config_mapping = json.load(f)

        settings = config_mapping.get("settings", {})
        mappings = config_mapping.get("mappings", {})

        es.indices.create(
            index=nome_indice,
            settings=settings,
            mappings=mappings,
        )
        logger.info(f"Índice '{nome_indice}' criado com sucesso com configurações de idioma PT-BR!")
    except ApiError as err:
        logger.error(f"Erro ao inicializar índice no Elasticsearch: {err}")
        sys.exit(1)


# Conexão com kafka consumer
def criar_consumidor_kafka(
    servers: str, topico: str, grupo: str, max_tentativas: int = 15, espera_seg: int = 4
) -> KafkaConsumer:
    logger.info(f"Conectando ao Kafka Consumer em {servers} (Tópico: {topico}, Grupo: {grupo})")
    for tentativa in range(1, max_tentativas + 1):
        try:
            consumidor = KafkaConsumer(
                topico,
                bootstrap_servers=servers.split(","),
                group_id=grupo,
                auto_offset_reset="earliest",
                enable_auto_commit=False, 
                consumer_timeout_ms=1000,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                key_deserializer=lambda k: k.decode("utf-8") if k else None,
            )
            logger.info("Conexão com Kafka Consumer estabelecida com sucesso.")
            return consumidor
        except KafkaError as err:
            logger.warning(
                f"Tentativa {tentativa}/{max_tentativas} de conexão com Kafka falhou: {err}. "
                f"Aguardando {espera_seg}s..."
            )
            time.sleep(espera_seg)

    logger.error("Falha crítica: Não foi possível conectar ao broker Kafka.")
    sys.exit(1)


# Loop de consumo e indexação
def executar_consumo():
    es = obter_cliente_elasticsearch(ELASTICSEARCH_URL)
    inicializar_indice(es, INDEX_NAME, MAPPING_FILE_PATH)
    consumidor = criar_consumidor_kafka(KAFKA_BOOTSTRAP_SERVERS, TOPIC_NAME, CONSUMER_GROUP_ID)

    total_indexados = 0
    total_erros = 0

    logger.info(f"Aguardando mensagens do tópico '{TOPIC_NAME}' para indexação no Elasticsearch...")

    try:
        while executando:
            lote = consumidor.poll(timeout_ms=1000)
            if not lote:
                continue

            for particao_topico, mensagens in lote.items():
                for mensagem in mensagens:
                    doc: Dict[str, Any] = mensagem.value
                    chave_kafka = mensagem.key
                    doc_id = doc.get("id") or chave_kafka

                    if not doc_id:
                        logger.error(f"Mensagem sem identificador válido descartada: {doc}")
                        total_erros += 1
                        continue

                    try:
                        resposta = es.index(
                            index=INDEX_NAME,
                            id=doc_id,
                            document=doc,
                        )
                        resultado = resposta.get("result", "indexed")

                        consumidor.commit()
                        total_indexados += 1

                        logger.info(
                            f"[ES INDEXADO] ID: {doc_id} | Ação: {resultado} | "
                            f"Kafka Offset: {mensagem.offset} (Partição {mensagem.partition})"
                        )
                    except ApiError as es_err:
                        logger.error(f"Erro ao indexar documento {doc_id} no Elasticsearch: {es_err}")
                        total_erros += 1
                    except Exception as gen_err:
                        logger.error(f"Erro inesperado no processamento do documento {doc_id}: {gen_err}")
                        total_erros += 1
    except Exception as e:
        logger.error(f"Exceção durante a execução do consumidor: {e}")
    finally:
        logger.info("Fechando conexões do consumidor...")
        consumidor.close()
        es.close()
        logger.info(
            f"Consumidor finalizado. Total indexados nesta sessão: {total_indexados} | Erros: {total_erros}"
        )


if __name__ == "__main__":
    executar_consumo()

