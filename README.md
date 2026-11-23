# ENADE HUB

Plataforma distribuída de busca, indexação e consulta de questões do acervo histórico do Exame Nacional de Desempenho dos Estudantes (ENADE).

## Sobre o projeto

O ENADE HUB é um projeto acadêmico desenvolvido para a disciplina de Big Data da UniCatólica de Quixadá. Seu objetivo é organizar e disponibilizar questões do ENADE por meio de uma arquitetura distribuída, permitindo buscas textuais, aplicação de filtros e gerenciamento de simulados.

## Arquitetura

O sistema utiliza os seguintes componentes:

1. **Ingestão:** coleta e processamento dos documentos e questões.
2. **Apache Kafka:** mensageria e comunicação entre os serviços.
3. **Elasticsearch:** indexação e busca dos documentos.
4. **FastAPI:** disponibilização dos recursos por meio de uma API REST.
5. **Redis:** armazenamento de sessões e simulados.
6. **Frontend:** interface web para consulta e gerenciamento de questões.

Fluxo principal:

`Ingestão → Kafka → Elasticsearch → API / Redis → Frontend`

## Tecnologias utilizadas

| Tecnologia | Finalidade |
|---|---|
| React | Construção da interface |
| Vite | Ambiente de desenvolvimento do frontend |
| JavaScript | Lógica da aplicação web |
| Python / FastAPI | API REST |
| Apache Kafka | Mensageria |
| Elasticsearch | Indexação e busca |
| Redis | Cache e gerenciamento de sessões |
| Docker | Execução dos serviços |

## Funcionalidades implementadas

### Interface web
- Página inicial e navegação entre módulos.
- Busca de questões integrada à API.
- Consulta de detalhes das questões.
- Exibição de metadados e alternativas.
- Adição e remoção de questões do simulado.
- Visualização do simulado.
- Exportação de simulados em PDF e JSON.

### Backend e processamento
- Processamento e publicação de questões no Kafka.
- Consumo de mensagens e indexação no Elasticsearch.
- Busca textual e filtros.
- Paginação dos resultados.
- Agregações estatísticas.
- Gerenciamento de simulados com Redis.
- Exportação de simulados.

## Como executar

### 1. Pré-requisitos

- Docker Desktop
- Node.js
- npm

### 2. Configurar as variáveis de ambiente

Copie o modelo e preencha os valores (qualquer valor serve em ambiente local de teste; o arquivo `.env` não vai para o Git):

```bash
cp .env.example .env
```

| Variável | Para que serve |
|---|---|
| `LDAP_ADMIN_PASSWORD` | Senha do administrador do OpenLDAP |
| `JWT_SECRET` | Segredo usado para assinar os tokens de login (gere com `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `KERBEROS_MASTER_PASSWORD` | Senha mestra do banco do KDC Kerberos |

### 3. Iniciar os serviços

Na raiz do projeto, execute:

```bash
docker compose up -d --build
```

### 4. Iniciar o frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

O Vite informará o endereço local para acessar a aplicação, normalmente:

`http://localhost:5173`

### 5. Acessar a documentação da API

Com os serviços ativos:

- API: `http://localhost:8001`
- Swagger: `http://localhost:8001/docs`
- Health check: `http://localhost:8001/health`

## Estrutura do projeto

```text
TP2-BigData/
├── api/
├── extraction/
├── frontend/
│   ├── public/
│   └── src/
│       ├── assets/
│       ├── pages/
│       ├── services/
│       ├── App.jsx
│       └── main.jsx
├── data/
├── docker-compose.yml
└── README.md
```

## Segurança

A plataforma separa a autenticação de **pessoas** da autenticação de **serviços**:

| Camada | Mecanismo | Onde atua |
|---|---|---|
| Usuários | LDAP (OpenLDAP) + token JWT | Login na API e no frontend |
| Perfis | Grupos do LDAP: `estudantes` e `professores` | Define o perfil `Estudante` ou `Professor` |
| Autorização | 401 sem token válido; 403 para perfil sem permissão | Rotas restritas ao professor |
| Serviços | Kerberos (KDC MIT, realm `ENADE.LOCAL`) com SASL/GSSAPI | Producer e consumer no Kafka |

### Usuários de demonstração (LDAP)

Credenciais apenas de laboratório, definidas em `ldap/bootstrap.ldif`. Não use em produção.

| Usuário | Senha | Perfil |
|---|---|---|
| `aluno1`, `aluno2` | `aluno123` | Estudante |
| `prof1` | `prof123` | Professor |

### Rotas e perfis

- `POST /api/v1/auth/login`: valida usuário e senha no LDAP e devolve um token JWT com o perfil.
- `GET /api/v1/auth/me`: mostra o usuário do token.
- Busca e detalhe de questões: abertas; o `Estudante` recebe a versão sem gabarito.
- `GET /api/v1/questoes/agregacoes/estatisticas` e exportação de simulados: somente `Professor`. O `Estudante` recebe **403**.

### Kerberos no Kafka

O serviço `kdc` cria as identidades `kafka/kafka`, `producer` e `consumer` e grava os keytabs em um volume Docker (`kerberos_keytabs`), fora do Git. O Kafka só aceita conexões com ticket Kerberos válido.

Para verificar:

```bash
docker compose ps
docker compose logs kafka-producer kafka-consumer | Select-String "GSSAPI"
```

O `enade-kdc` deve estar `Healthy` e os logs devem mostrar `Authenticated as kafka/kafka@ via GSSAPI`. Sem Kerberos, o broker recusa a conexão (`KafkaTimeoutError` ao pedir os metadados).

### Limitações conhecidas

- O Elasticsearch roda com a segurança desativada nesta versão. A autenticação Kerberos no Elasticsearch exige licença paga ou período de teste, e não está disponível na licença Basic gratuita.
- Os listeners usam `SASL_PLAINTEXT` (autenticação sem criptografia de transporte). Em produção, usar `SASL_SSL`.
- Os keytabs ficam legíveis por todos os containers (permissão 644) para simplificar o ambiente de laboratório.

## Equipe e contexto acadêmico

Projeto TP2 — Disciplina de Big Data  
UniCatólica de Quixadá  
Docente: Prof. Me. Décio Aguiar


