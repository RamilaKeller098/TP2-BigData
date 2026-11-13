import io
from typing import Any, Dict, List
from fastapi import APIRouter, Header, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse, Response
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from api.services.redis_service import redis_service

router = APIRouter(prefix="/api/v1/simulados", tags=["Simulados / Exportação"])


def validar_permissao_professor(role: str):
    """
    - Acesso restrito a professores.
    - Tentativa de acesso por estudante resulta obrigatoriamente em 403 (Forbidden).
    """

    if role.strip().capitalize() != "Professor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: Somente usuários com perfil 'Professor' podem exportar simulados e gabaritos.",
        )


# Exportar em JSON

@router.get(
    "/exportar/json/{session_id}",
    summary="Exportar simulado em formato JSON",
    description="Exporta a lista de questões da sessão em JSON. Restrito a professores.",
)
def exportar_json(
    session_id: str = Path(..., description="ID da sessão do carrinho"),
    x_user_role: str = Header("Estudante", alias="X-User-Role"),
):
    validar_permissao_professor(x_user_role)

    questoes = redis_service.obter_carrinho(session_id)
    if not questoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O carrinho da sessão está vazio. Adicione questões antes de exportar.",
        )

    payload = {
        "titulo": "Simulado ENADE Personalizado",
        "session_id": session_id,
        "total_questoes": len(questoes),
        "questoes": questoes,
    }
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f"attachment; filename=simulado_{session_id}.json"},
    )


# Exportar em PDF

@router.get(
    "/exportar/pdf/{session_id}",
    summary="Exportar simulado em formato PDF",
    description="Gera documento PDF paginado e diagramado com as questões selecionadas.",
)
def exportar_pdf(
    session_id: str = Path(..., description="ID da sessão do carrinho"),
    incluir_gabarito: bool = Query(True, description="Incluir folha de respostas ao final"),
    x_user_role: str = Header("Estudante", alias="X-User-Role"),
):
    validar_permissao_professor(x_user_role)

    questoes = redis_service.obter_carrinho(session_id)
    if not questoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O carrinho da sessão está vazio. Adicione questões antes de exportar.",
        )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        "Titulo",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        spaceAfter=12,
    )
    subtitulo_style = ParagraphStyle(
        "Subtitulo",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor="#555555",
        spaceAfter=18,
    )
    questao_header_style = ParagraphStyle(
        "QuestaoHeader",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
    )
    corpo_style = ParagraphStyle(
        "Corpo",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )
    alt_style = ParagraphStyle(
        "Alternativa",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13,
        leftIndent=15,
        spaceAfter=3,
    )

    story = [
        Paragraph("SIMULADO ENADE PERSONALIZADO", titulo_style),
        Paragraph(
            f"Gerado via Plataforma Distribuída ENADE | Total de Questões: {len(questoes)}",
            subtitulo_style,
        ),
        Spacer(1, 10),
    ]

    for idx, q in enumerate(questoes, start=1):
        num_orig = q.get("numero") or q.get("numero_discursiva")
        curso = q.get("curso", "ENADE")
        ano = q.get("ano", "")
        secao = q.get("secao", "")
        tipo = q.get("tipo_questao", "").capitalize()

        story.append(
            Paragraph(
                f"<b>Questão {idx}</b> ({curso} {ano} - {secao} / {tipo} - Original: Q{num_orig})",
                questao_header_style,
            )
        )

        enunciado = q.get("enunciado", "").replace("\n", "<br/>")
        story.append(Paragraph(enunciado, corpo_style))
        story.append(Spacer(1, 4))

        alternativas = q.get("alternativas", [])
        for alt in alternativas:
            letra = alt.get("letra", "")
            txt = alt.get("texto", "").replace("\n", " ")
            story.append(Paragraph(f"<b>({letra})</b> {txt}", alt_style))

        story.append(Spacer(1, 14))

    # Folha de gabarito ao final - para os professores

    if incluir_gabarito:
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>GABARITO OFICIAL</b>", questao_header_style))
        for idx, q in enumerate(questoes, start=1):
            gab = q.get("gabarito", "Discursiva")
            story.append(
                Paragraph(f"Questão {idx}: <b>{gab}</b>", corpo_style)
            )

    doc.build(story)
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=simulado_{session_id}.pdf"
        },
    )

