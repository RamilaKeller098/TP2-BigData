import logging
from typing import Any, Dict, List, Optional, Tuple
from elasticsearch import Elasticsearch, NotFoundError
from api.config import ELASTICSEARCH_INDEX, ELASTICSEARCH_URL

logger = logging.getLogger("api-elasticsearch")


class ElasticsearchService:
    def __init__(self, url: str = ELASTICSEARCH_URL, index_name: str = ELASTICSEARCH_INDEX):
        self.url = url
        self.index_name = index_name
        self.client = Elasticsearch(self.url, request_timeout=15)

    def ping(self) -> bool:
        try:
            return bool(self.client.ping())
        except Exception as e:
            logger.error(f"Erro ao conectar com Elasticsearch: {e}")
            return False

    def obter_por_id(self, questao_id: str) -> Optional[Dict[str, Any]]:
        try:
            resp = self.client.get(index=self.index_name, id=questao_id)
            return resp.get("_source")
        except NotFoundError:
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar questão {questao_id}: {e}")
            return None

    def buscar_questoes(
        self,
        termo: Optional[str] = None,
        area: Optional[str] = None,
        curso: Optional[str] = None,
        ano: Optional[int] = None,
        tipo_questao: Optional[str] = None,
        secao: Optional[str] = None,
        competencia: Optional[str] = None,
        page: int = 1,
        size: int = 10,
    ) -> Dict[str, Any]:
        must_clauses: List[Dict[str, Any]] = []
        filter_clauses: List[Dict[str, Any]] = []

        if termo and termo.strip():
            must_clauses.append(
                {
                    "multi_match": {
                        "query": termo.strip(),
                        "fields": [
                            "enunciado^3",
                            "texto_completo^2",
                            "curso",
                            "area",
                        ],
                        "analyzer": "enade_pt_analyzer",
                    }
                }
            )
        else:
            must_clauses.append({"match_all": {}})

        # Filtros estruturados

        if area:
            filter_clauses.append({"term": {"area.keyword": area}})
        if curso:
            filter_clauses.append({"term": {"curso.keyword": curso}})
        if ano:
            filter_clauses.append({"term": {"ano": ano}})
        if tipo_questao:
            filter_clauses.append({"term": {"tipo_questao": tipo_questao.lower()}})
        if secao:
            filter_clauses.append({"term": {"secao": secao.upper()}})
        if competencia:
            filter_clauses.append({"term": {"competencias": competencia}})

        query_body: Dict[str, Any] = {
            "query": {
                "bool": {
                    "must": must_clauses,
                    "filter": filter_clauses,
                }
            },
            "from": (page - 1) * size,
            "size": size,
            "highlight": {
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"],
                "fields": {
                    "enunciado": {"number_of_fragments": 2, "fragment_size": 150},
                    "texto_completo": {"number_of_fragments": 2, "fragment_size": 150},
                },
            },
        }

        try:
            resposta = self.client.search(index=self.index_name, body=query_body)
            total_hits = resposta["hits"]["total"]["value"]

            itens = []
            for hit in resposta["hits"]["hits"]:
                doc = hit["_source"]
                destaques = hit.get("highlight", {})
                doc["highlights"] = destaques
                itens.append(doc)

            total_paginas = (total_hits + size - 1) // size if total_hits > 0 else 1

            return {
                "total": total_hits,
                "pagina_atual": page,
                "tamanho_pagina": size,
                "total_paginas": total_paginas,
                "questoes": itens,
            }
        except Exception as e:
            logger.error(f"Erro na busca do Elasticsearch: {e}")
            raise e

    # Agregações analíticas

    def obter_agregacoes(self) -> Dict[str, Any]:
        """
        Calcula distribuições quantitativas por curso e agregações temporais/competências.
        """
        query_body = {
            "size": 0,
            "aggs": {
                "distribuicao_cursos": {
                    "terms": {"field": "curso.keyword", "size": 50}
                },
                "distribuicao_areas": {
                    "terms": {"field": "area.keyword", "size": 50}
                },
                "distribuicao_anos": {
                    "terms": {"field": "ano", "size": 20},
                    "aggs": {
                        "competencias": {
                            "terms": {"field": "competencias", "size": 20}
                        }
                    },
                },
                "distribuicao_tipos": {
                    "terms": {"field": "tipo_questao", "size": 10}
                },
                "distribuicao_secoes": {
                    "terms": {"field": "secao", "size": 10}
                },
            },
        }
        try:
            resposta = self.client.search(index=self.index_name, body=query_body)
            aggs = resposta.get("aggregations", {})

            return {
                "por_curso": [
                    {"curso": b["key"], "quantidade": b["doc_count"]}
                    for b in aggs.get("distribuicao_cursos", {}).get("buckets", [])
                ],
                "por_area": [
                    {"area": b["key"], "quantidade": b["doc_count"]}
                    for b in aggs.get("distribuicao_areas", {}).get("buckets", [])
                ],
                "por_ano": [
                    {
                        "ano": b["key"],
                        "quantidade": b["doc_count"],
                        "competencias": [
                            {"competencia": c["key"], "quantidade": c["doc_count"]}
                            for c in b.get("competencias", {}).get("buckets", [])
                        ],
                    }
                    for b in aggs.get("distribuicao_anos", {}).get("buckets", [])
                ],
                "por_tipo": [
                    {"tipo": b["key"], "quantidade": b["doc_count"]}
                    for b in aggs.get("distribuicao_tipos", {}).get("buckets", [])
                ],
                "por_secao": [
                    {"secao": b["key"], "quantidade": b["doc_count"]}
                    for b in aggs.get("distribuicao_secoes", {}).get("buckets", [])
                ],
            }
        except Exception as e:
            logger.error(f"Erro ao calcular agregações no Elasticsearch: {e}")
            raise e




es_service = ElasticsearchService()