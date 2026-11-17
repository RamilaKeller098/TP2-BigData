"""Autenticação de usuários no servidor LDAP e descoberta do perfil (RF23/RF24)."""
import logging
from typing import Optional

from ldap3 import SUBTREE, Connection, Server
from ldap3.core.exceptions import LDAPException
from ldap3.utils.conv import escape_filter_chars
from ldap3.utils.dn import escape_rdn

from api.config import (
    LDAP_ADMIN_DN,
    LDAP_ADMIN_PASSWORD,
    LDAP_BASE_DN,
    LDAP_GRUPO_ESTUDANTES,
    LDAP_GRUPO_PROFESSORES,
    LDAP_HOST,
    LDAP_PORT,
)

logger = logging.getLogger(__name__)


class LdapIndisponivel(Exception):
    """O servidor LDAP não respondeu ou a conta de serviço foi recusada."""


class LdapService:
    def __init__(self) -> None:
        self.server = Server(LDAP_HOST, port=LDAP_PORT, connect_timeout=5)

    def _dn_usuario(self, usuario: str) -> str:
        # escape_rdn evita injeção no DN (ex.: usuario = "x,ou=groups")
        return f"uid={escape_rdn(usuario)},ou=people,{LDAP_BASE_DN}"

    def autenticar(self, usuario: str, senha: str) -> Optional[str]:
        """
        Retorna "Professor", "Estudante" ou None (credencial inválida ou usuário
        fora dos grupos esperados). Levanta LdapIndisponivel se o LDAP cair.
        """
        # Senha vazia vira "bind anônimo" no LDAP e seria aceita: bloquear sempre.
        if not usuario or not senha:
            return None

        dn = self._dn_usuario(usuario)

        # 1) valida a senha tentando o bind com as credenciais do próprio usuário
        try:
            conn = Connection(self.server, user=dn, password=senha, receive_timeout=5)
            try:
                if not conn.bind():
                    return None
            finally:
                conn.unbind()
        except LDAPException as exc:
            logger.error("LDAP indisponível durante o bind do usuário: %s", exc)
            raise LdapIndisponivel(str(exc)) from exc

        # 2) descobre os grupos do usuário com a conta de serviço (admin)
        try:
            admin = Connection(
                self.server, user=LDAP_ADMIN_DN, password=LDAP_ADMIN_PASSWORD,
                receive_timeout=5,
            )
            try:
                if not admin.bind():
                    raise LdapIndisponivel("Conta de serviço do LDAP recusada.")
                admin.search(
                    search_base=f"ou=groups,{LDAP_BASE_DN}",
                    search_filter=(
                        "(&(objectClass=groupOfNames)"
                        f"(member={escape_filter_chars(dn)}))"
                    ),
                    search_scope=SUBTREE,
                    attributes=["cn"],
                )
                grupos = {str(e.cn) for e in admin.entries}
            finally:
                admin.unbind()
        except LDAPException as exc:
            logger.error("LDAP indisponível durante a busca de grupos: %s", exc)
            raise LdapIndisponivel(str(exc)) from exc

        if LDAP_GRUPO_PROFESSORES in grupos:
            return "Professor"
        if LDAP_GRUPO_ESTUDANTES in grupos:
            return "Estudante"
        return None


ldap_service = LdapService()
