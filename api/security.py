"""JWT + dependências de autorização do FastAPI (RF24/RF25)."""
import time
from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.config import JWT_ALGORITMO, JWT_EXPIRA_MINUTOS, JWT_SECRET

# auto_error=False: a gente decide se a falta de token é erro (401) ou não
_bearer = HTTPBearer(auto_error=False, description="Token obtido em POST /api/v1/auth/login")


@dataclass
class Usuario:
    username: str
    role: str  # "Estudante" ou "Professor"


def criar_token(username: str, role: str) -> tuple[str, int]:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET não configurado (defina no .env).")
    agora = int(time.time())
    exp = agora + JWT_EXPIRA_MINUTOS * 60
    token = jwt.encode(
        {"sub": username, "role": role, "iat": agora, "exp": exp},
        JWT_SECRET,
        algorithm=JWT_ALGORITMO,
    )
    return token, JWT_EXPIRA_MINUTOS * 60


def _decodificar(token: str) -> Usuario:
    try:
        # algorithms=[...] fixo: nunca aceitar o algoritmo que vem no token
        dados = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITMO])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Usuario(username=dados["sub"], role=dados["role"])


def usuario_atual(
    cred: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Usuario:
    """Exige login. Sem token ou token ruim => 401."""
    if cred is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _decodificar(cred.credentials)


def usuario_opcional(
    cred: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Usuario:
    """
    Rotas públicas de busca: sem token vira Estudante anônimo (sem gabarito).
    Token presente mas inválido continua dando 401 (não rebaixa em silêncio).
    """
    if cred is None:
        return Usuario(username="anonimo", role="Estudante")
    return _decodificar(cred.credentials)


def exigir_professor(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
    """Rotas restritas. Logado como Estudante => 403 (RF25)."""
    if usuario.role != "Professor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: esta rota é restrita ao perfil 'Professor'.",
        )
    return usuario
