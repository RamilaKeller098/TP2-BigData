#!/bin/sh
# KDC do realm ENADE.LOCAL: cria o banco, as identidades dos serviços e os keytabs.
# Os keytabs ficam em um volume Docker (/keytabs), nunca no Git.
set -eu

: "${KRB5_MASTER_PASSWORD:?Defina KERBEROS_MASTER_PASSWORD no arquivo .env}"

REALM="ENADE.LOCAL"
DB="/var/lib/krb5kdc/principal"
KEYTABS="/keytabs"

mkdir -p /var/lib/krb5kdc "$KEYTABS"
rm -f "$KEYTABS/.ready"

if [ ! -f "$DB" ]; then
    echo "[kdc] Criando banco de dados do realm $REALM"
    kdb5_util create -r "$REALM" -s -P "$KRB5_MASTER_PASSWORD"
fi

# criar_servico <principal> <arquivo.keytab>
# Só gera o keytab se ele ainda não existir (evita invalidar chaves em uso).
criar_servico() {
    principal="$1"
    arquivo="$2"
    if [ ! -f "$KEYTABS/$arquivo" ]; then
        echo "[kdc] Criando $principal"
        kadmin.local -q "addprinc -randkey $principal" || true
        kadmin.local -q "ktadd -k $KEYTABS/$arquivo $principal"
        # Permissão aberta para os containers (usuários diferentes) lerem. Ambiente de laboratório.
        chmod 644 "$KEYTABS/$arquivo"
    fi
}

criar_servico "kafka/kafka@$REALM" "kafka.keytab"
criar_servico "producer@$REALM"    "producer.keytab"
criar_servico "consumer@$REALM"    "consumer.keytab"

touch "$KEYTABS/.ready"
echo "[kdc] Pronto. Iniciando krb5kdc."
exec krb5kdc -n
