import os

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX_NAME", "enade-questoes")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))
CARRINHO_TTL_SECONDS = int(os.getenv("CARRINHO_TTL_SECONDS", "86400"))  # 24 horas

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# LDAP (RF23)
LDAP_HOST = os.getenv("LDAP_HOST", "localhost")
LDAP_PORT = int(os.getenv("LDAP_PORT", "389"))
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "dc=enade,dc=local")
LDAP_ADMIN_DN = os.getenv("LDAP_ADMIN_DN", f"cn=admin,{LDAP_BASE_DN}")
LDAP_ADMIN_PASSWORD = os.getenv("LDAP_ADMIN_PASSWORD", "")
LDAP_GRUPO_PROFESSORES = os.getenv("LDAP_GRUPO_PROFESSORES", "professores")
LDAP_GRUPO_ESTUDANTES = os.getenv("LDAP_GRUPO_ESTUDANTES", "estudantes")

# JWT (RF24)
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITMO = "HS256"
JWT_EXPIRA_MINUTOS = int(os.getenv("JWT_EXPIRA_MINUTOS", "60"))
