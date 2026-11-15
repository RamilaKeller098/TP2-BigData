from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Header, HTTPException, Query, status
from api.services.elasticsearch_service import es_service
from api.services.redis_service import redis_service

router = APIRouter(prefix="/api/v1/questoes", tags=["Questões"])


def sanitizar_por_perfil(questao: Dict[str, Any], role: str) -> Dict[str, Any]:
    """
    - Perfil Estudante não tem acesso a gabaritos restritos.
    - Perfil Professor tem visualização completa.
    """

    copia = dict(questao)
    if role.strip().capitalize() != "Professor":
        copia["gabarito"] = None
    return copia


@router.get(
    "/busca",
    summary="Busca full-text com filtros estruturados e cache",
    description="Pesquisa no acervo ENADE com suporte a PT-BR, sinônimos, realce e cache Redis.",
)
def buscar_questoes(
    q: Optional[str] = Query(None, description="Termo de busca textual"),
    area: Optional[str] = Query(None, description="Área do conhecimento"),
    curso: Optional[str] = Query(None, description="Nome do curso"),
    ano: Optional[int] = Query(None, description="Ano da edição"),
    tipo_questao: Optional[str] = Query(None, description="Tipo: 'objetiva' ou 'discursiva'"),
    secao: Optional[str] = Query(None, description="Seção: 'FG' ou 'CE'"),
    competencia: Optional[str] = Query(None, description="Competência específica"),
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(10, ge=1, le=100, description="Quantidade por página"),
    x_user_role: str = Header("Estudante", alias="X-User-Role", description="Perfil: 'Estudante' ou 'Professor'"),
):
    params_busca = {
        "q": q,
        "area": area,
        "curso": curso,
        "ano": ano,
        "tipo_questao": tipo_questao,
        "secao": secao,
        "competencia": competencia,
        "page": page,
        "size": size,
    }

    # Verificação de cache no redis
    chave_cache = redis_service.gerar_chave_cache("busca", params_busca)
    dados_cacheados = redis_service.obter_cache(chave_cache)

    if dados_cacheados:
        # sanitização de perfil
        dados_cacheados["questoes"] = [
            sanitizar_por_perfil(q_item, x_user_role) for q_item in dados_cacheados["questoes"]
        ]
        dados_cacheados["cache_hit"] = True
        return dados_cacheados

    try:
        resultado = es_service.buscar_questoes(
            termo=q,
            area=area,
            curso=curso,
            ano=ano,
            tipo_questao=tipo_questao,
            secao=secao,
            competencia=competencia,
            page=page,
            size=size,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao consultar motor de busca: {str(e)}",
        )

    redis_service.salvar_cache(chave_cache, resultado)

    resultado["questoes"] = [
        sanitizar_por_perfil(q_item, x_user_role) for q_item in resultado["questoes"]
    ]
    resultado["cache_hit"] = False
    return resultado


# Agregações analíticas

@router.get(
    "/agregacoes/estatisticas",
    summary="Agregações quantitativas e histogramas",
    description="Retorna distribuições por curso, área, tipo, seção e histograma de competências por ano.",
)
def obter_agregacoes(
    x_user_role: str = Header("Estudante", alias="X-User-Role"),
):
    chave_cache = "agregacoes:geral"
    dados_cacheados = redis_service.obter_cache(chave_cache)
    if dados_cacheados:
        dados_cacheados["cache_hit"] = True
        return dados_cacheados

    try:
        dados = es_service.obter_agregacoes()
        redis_service.salvar_cache(chave_cache, dados, ttl=600)
        dados["cache_hit"] = False
        return dados
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao gerar agregações analíticas: {str(e)}",
        )


# Questão por ID

@router.get(
    "/{questao_id}",
    summary="Obter questão por ID",
    description="Busca uma questão individual pelo seu identificador único.",
)
def obter_questao(
    questao_id: str,
    x_user_role: str = Header("Estudante", alias="X-User-Role"),
):
    doc = es_service.obter_por_id(questao_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questão '{questao_id}' não encontrada no acervo.",
        )
    return sanitizar_por_perfil(doc, x_user_role)

