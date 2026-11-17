from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.security import Usuario, criar_token, usuario_atual
from api.services.ldap_service import LdapIndisponivel, ldap_service

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])


class LoginRequest(BaseModel):
    usuario: str
    senha: str


@router.post(
    "/login",
    summary="Login via LDAP",
    description="Valida usuário e senha no servidor LDAP e devolve um token JWT com o perfil.",
)
def login(dados: LoginRequest):
    try:
        perfil = ldap_service.autenticar(dados.usuario, dados.senha)
    except LdapIndisponivel:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de autenticação indisponível. Tente novamente.",
        )

    if perfil is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token, expira_em = criar_token(dados.usuario, perfil)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expira_em_segundos": expira_em,
        "usuario": dados.usuario,
        "perfil": perfil,
    }


@router.get("/me", summary="Quem sou eu", description="Retorna o usuário e o perfil do token enviado.")
def me(usuario: Usuario = Depends(usuario_atual)):
    return {"usuario": usuario.username, "perfil": usuario.role}
