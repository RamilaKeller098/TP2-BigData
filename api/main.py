import logging
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from api.config import API_HOST, API_PORT
from api.routers import carrinho, questoes, simulados
from api.services.elasticsearch_service import es_service
from api.services.redis_service import redis_service

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Plataforma Distribuída de Busca do ENADE - API",
    description=(
        "API RESTful para busca full-text, filtros interdisciplinares, agregações, "
        "carrinho de questões em Redis e exportação de simulados."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS para o cliente web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers
app.include_router(questoes.router)
app.include_router(carrinho.router)
app.include_router(simulados.router)


# Endpoints health e observabilidade
@app.get(
    "/health",
    summary="Health check dos serviços",
    tags=["Observabilidade"],
    status_code=status.HTTP_200_OK,
)
def health_check():
    es_status = es_service.ping()
    redis_status = redis_service.ping()

    status_geral = "healthy" if (es_status and redis_status) else "unhealthy"

    return {
        "status": status_geral,
        "servicos": {
            "elasticsearch": "online" if es_status else "offline",
            "redis": "online" if redis_status else "offline",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host=API_HOST, port=API_PORT, reload=True)

