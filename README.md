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

### 2. Iniciar os serviços

Na raiz do projeto, execute:

```bash
docker compose up -d --build
```

### 3. Iniciar o frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

O Vite informará o endereço local para acessar a aplicação, normalmente:

`http://localhost:5173`

### 4. Acessar a documentação da API

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

## Desenvolvimento e segurança

O projeto está em desenvolvimento. A integração de autenticação LDAP, comunicação segura com Kerberos e controle definitivo de permissões fazem parte das atividades de segurança e integração da equipe.

Os perfis utilizados atualmente no frontend são destinados ao desenvolvimento e não substituem a autenticação real.

## Equipe e contexto acadêmico

Projeto TP2 — Disciplina de Big Data  
UniCatólica de Quixadá  
Docente: Prof. Me. Décio Aguiar


