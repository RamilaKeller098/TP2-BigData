from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Path, status
from api.services.elasticsearch_service import es_service
from api.services.redis_service import redis_service

router = APIRouter(prefix="/api/v1/carrinho", tags=["Carrinho / Sessão"])


@router.get(
    "/{session_id}",
    summary="Listar questões do carrinho",
    description="Recupera a lista de questões selecionadas na sessão atual persistida no Redis.",
)
def listar_carrinho(
    session_id: str = Path(..., description="Identificador da sessão do usuário")
) -> Dict[str, Any]:
    itens = redis_service.obter_carrinho(session_id)
    return {
        "session_id": session_id,
        "total_itens": len(itens),
        "questoes": itens,
    }


@router.post(
    "/{session_id}/adicionar/{questao_id}",
    summary="Adicionar questão ao carrinho",
    description="Insere uma questão do acervo no carrinho persistido da sessão.",
    status_code=status.HTTP_201_CREATED,
)
def adicionar_ao_carrinho(
    session_id: str = Path(..., description="Identificador da sessão"),
    questao_id: str = Path(..., description="ID da questão a ser adicionada"),
):
    # Obtém os dados completos da questão no elasticsearch
    questao = es_service.obter_por_id(questao_id)
    if not questao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questão '{questao_id}' não encontrada no acervo.",
        )

    sucesso = redis_service.adicionar_ao_carrinho(session_id, questao)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível salvar a questão no carrinho.",
        )

    return {
        "mensagem": f"Questão '{questao_id}' adicionada ao carrinho com sucesso.",
        "session_id": session_id,
        "questao_id": questao_id,
    }


@router.delete(
    "/{session_id}/remover/{questao_id}",
    summary="Remover questão do carrinho",
    description="Remove uma questão específica da sessão.",
)
def remover_do_carrinho(
    session_id: str = Path(...),
    questao_id: str = Path(...),
):
    sucesso = redis_service.remover_do_carrinho(session_id, questao_id)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questão '{questao_id}' não encontrada no carrinho da sessão.",
        )
    return {
        "mensagem": f"Questão '{questao_id}' removida com sucesso.",
        "session_id": session_id,
    }


@router.delete(
    "/{session_id}",
    summary="Limpar todo o carrinho",
    description="Esvazia todas as questões armazenadas na sessão.",
)
def limpar_carrinho(session_id: str = Path(...)):
    redis_service.limpar_carrinho(session_id)
    return {
        "mensagem": "Carrinho esvaziado com sucesso.",
        "session_id": session_id,
    }

