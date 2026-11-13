import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
from kafka import KafkaProducer
from kafka.errors import KafkaError

# ─── Configuração de Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("kafka-producer")

# ─── Variáveis de Ambiente e Configurações ────────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC_NAME = os.getenv("KAFKA_TOPIC_NAME", "enade-questoes")
DLQ_TOPIC_NAME = os.getenv("KAFKA_DLQ_TOPIC_NAME", "enade-questoes-dlq")
INPUT_JSON_PATH = os.getenv(
    "INPUT_JSON_PATH", "extraction/questoes_enriquecidas.json"
)
CHECKPOINT_PATH = os.getenv(
    "CHECKPOINT_PATH", "kafka/producer/checkpoint.json"
)

# Campos obrigatórios para validação de integridade (RF05, RF06, RF11)
CAMPOS_OBRIGATORIOS = [
    "id",
    "ano",
    "curso",
    "area",
    "secao",
    "tipo_questao",
    "enunciado",
    "pdf_origem",
    "pagina_inicio",
]


# ─── Controle de Checkpoint (RF09 - Tolerância a Falhas) ──────────────────────
def carregar_checkpoint(caminho: str) -> set:
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
                return set(dados.get("enviados", []))
        except Exception as e:
            logger.warning(f"Falha ao carregar checkpoint ({e}). Iniciando conjunto vazio.")
    return set()


def salvar_checkpoint(caminho: str, enviados: set):
    pasta = os.path.dirname(caminho)
    if pasta and not os.path.exists(pasta):
        os.makedirs(pasta, exist_ok=True)
    temp_path = f"{caminho}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump({"enviados": sorted(list(enviados))}, f, indent=2, ensure_ascii=False)
    os.replace(temp_path, caminho)


# ─── Validação de Mensagens (RF11 - Tratamento de Erros / DLQ) ────────────────
def validar_questao(questao: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    if not isinstance(questao, dict):
        return False, "O documento não é um objeto JSON válido."

    for campo in CAMPOS_OBRIGATORIOS:
        if campo not in questao or questao[campo] is None:
            return False, f"Campo obrigatório ausente ou nulo: '{campo}'"

    if questao.get("tipo_questao") == "objetiva":
        if not isinstance(questao.get("alternativas"), list) or len(questao["alternativas"]) == 0:
            return False, "Questão objetiva sem lista de alternativas válida."

    return True, None


# ─── Conexão Resiliente ao Kafka ──────────────────────────────────────────────
def criar_produtor(servers: str, max_tentativas: int = 10, espera_seg: int = 3) -> KafkaProducer:
    logger.info(f"Conectando ao Kafka em: {servers}")
    for tentativa in range(1, max_tentativas + 1):
        try:
            produtor = KafkaProducer(
                bootstrap_servers=servers.split(","),
                acks="all",              # Máxima durabilidade (RF09)
                retries=5,               # Retentativas automáticas
                key_serializer=lambda k: str(k).encode("utf-8"),
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
                max_in_flight_requests_per_connection=1,  # Preserva ordenação (RF10)
            )
            logger.info("Conexão com Kafka estabelecida com sucesso.")
            return produtor
        except KafkaError as err:
            logger.warning(f"Tentativa {tentativa}/{max_tentativas} falhou: {err}. Aguardando {espera_seg}s...")
            time.sleep(espera_seg)

    logger.error("Não foi possível conectar ao broker Kafka após várias tentativas.")
    sys.exit(1)


# ─── Fluxo Principal de Publicação ────────────────────────────────────────────
def executar_publicacao():
    if not os.path.exists(INPUT_JSON_PATH):
        logger.error(f"Arquivo de entrada não encontrado: {INPUT_JSON_PATH}")
        sys.exit(1)

    with open(INPUT_JSON_PATH, "r", encoding="utf-8") as f:
        questoes: List[Dict[str, Any]] = json.load(f)

    logger.info(f"Carregadas {len(questoes)} questões do arquivo {INPUT_JSON_PATH}.")

    enviados_checkpoint = carregar_checkpoint(CHECKPOINT_PATH)
    logger.info(f"Checkpoint carregado: {len(enviados_checkpoint)} itens já publicados anteriormente.")

    produtor = criar_produtor(KAFKA_BOOTSTRAP_SERVERS)

    total_sucesso = 0
    total_dlq = 0
    total_ignorados = 0

    try:
        for idx, questao in enumerate(questoes, start=1):
            doc_id = questao.get("id", f"desconhecido_{idx}")

            # Idempotência / Retomada exata (RF09, RF10)
            if doc_id in enviados_checkpoint:
                total_ignorados += 1
                continue

            eh_valido, motivo_erro = validar_questao(questao)

            if eh_valido:
                # Publicação no tópico principal com chave = doc_id (RF07, RF10)
                futuro = produtor.send(
                    topic=TOPIC_NAME,
                    key=doc_id,
                    value=questao,
                )
                record_metadata = futuro.get(timeout=10)
                enviados_checkpoint.add(doc_id)
                salvar_checkpoint(CHECKPOINT_PATH, enviados_checkpoint)
                total_sucesso += 1
                logger.info(
                    f"[SUCESSO] ID: {doc_id} -> Tópico: {record_metadata.topic} "
                    f"[Partição: {record_metadata.partition}, Offset: {record_metadata.offset}]"
                )
            else:
                # Roteamento para DLQ com detalhes do erro (RF11)
                dlq_payload = {
                    "documento_original": questao,
                    "erro": motivo_erro,
                    "timestamp": time.time(),
                }
                futuro = produtor.send(
                    topic=DLQ_TOPIC_NAME,
                    key=doc_id,
                    value=dlq_payload,
                )
                record_metadata = futuro.get(timeout=10)
                enviados_checkpoint.add(doc_id)
                salvar_checkpoint(CHECKPOINT_PATH, enviados_checkpoint)
                total_dlq += 1
                logger.warning(
                    f"[DLQ] ID: {doc_id} encaminhado para {DLQ_TOPIC_NAME} devido a: {motivo_erro}"
                )

        produtor.flush()
    except Exception as e:
        logger.error(f"Erro inesperado durante a execução do pipeline de publicação: {e}")
        raise
    finally:
        produtor.close()

    logger.info("=== Resumo da Execução do Produtor Kafka ===")
    logger.info(f"  Publicados com sucesso: {total_sucesso}")
    logger.info(f"  Enviados para DLQ:      {total_dlq}")
    logger.info(f"  Ignorados (checkpoint): {total_ignorados}")
    logger.info(f"  Total no checkpoint:    {len(enviados_checkpoint)}")


if __name__ == "__main__":
    executar_publicacao()

