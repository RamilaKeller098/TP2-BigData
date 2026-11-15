import hashlib
import json
import logging
from typing import Any, Dict, List, Optional
import redis
from api.config import CACHE_TTL_SECONDS, CARRINHO_TTL_SECONDS, REDIS_URL

logger = logging.getLogger("api-redis")


class RedisService:
    def __init__(self, url: str = REDIS_URL):
        self.client = redis.from_url(url, decode_responses=True)

    def ping(self) -> bool:
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Erro ao conectar com Redis: {e}")
            return False

    # Cache de consultas

    @staticmethod
    def gerar_chave_cache(prefixo: str, params: Dict[str, Any]) -> str:
        """Gera chave determinística com hash MD5 dos parâmetros de busca."""
        ordenado = json.dumps(params, sort_keys=True, ensure_ascii=False)
        hash_digest = hashlib.md5(ordenado.encode("utf-8")).hexdigest()
        return f"{prefixo}:{hash_digest}"

    def obter_cache(self, chave: str) -> Optional[Dict[str, Any]]:
        try:
            conteudo = self.client.get(chave)
            if conteudo:
                return json.loads(conteudo)
        except Exception as e:
            logger.warning(f"Falha ao ler cache Redis (chave: {chave}): {e}")
        return None

    def salvar_cache(
        self, chave: str, dados: Dict[str, Any], ttl: int = CACHE_TTL_SECONDS
    ):
        try:
            self.client.setex(chave, ttl, json.dumps(dados, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"Falha ao salvar cache Redis (chave: {chave}): {e}")

    # Carrinho de questões
    def obter_chave_carrinho(self, session_id: str) -> str:
        return f"carrinho:{session_id}"

    def obter_carrinho(self, session_id: str) -> List[Dict[str, Any]]:
        chave = self.obter_chave_carrinho(session_id)
        try:
            itens = self.client.hgetall(chave)
            if not itens:
                return []
            return [json.loads(val) for val in itens.values()]
        except Exception as e:
            logger.error(f"Erro ao recuperar carrinho ({session_id}): {e}")
            return []

    def adicionar_ao_carrinho(
        self, session_id: str, questao: Dict[str, Any]
    ) -> bool:
        chave = self.obter_chave_carrinho(session_id)
        questao_id = questao.get("id")
        if not questao_id:
            return False
        try:
            self.client.hset(chave, questao_id, json.dumps(questao, ensure_ascii=False))
            self.client.expire(chave, CARRINHO_TTL_SECONDS)
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar item ao carrinho ({session_id}): {e}")
            return False

    def remover_do_carrinho(self, session_id: str, questao_id: str) -> bool:
        chave = self.obter_chave_carrinho(session_id)
        try:
            removido = self.client.hdel(chave, questao_id)
            return bool(removido)
        except Exception as e:
            logger.error(f"Erro ao remover item do carrinho ({session_id}): {e}")
            return False

    def limpar_carrinho(self, session_id: str) -> bool:
        chave = self.obter_chave_carrinho(session_id)
        try:
            self.client.delete(chave)
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar carrinho ({session_id}): {e}")
            return False




redis_service = RedisService()