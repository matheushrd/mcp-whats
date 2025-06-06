# MCP Platform - Multi-Client Platform

Sistema de orquestração para gerenciamento de múltiplos clientes em Kubernetes com integração WhatsApp Business, Google Calendar e Gemini AI.

## 📋 Visão Geral

O MCP Platform automatiza a criação e gerenciamento de ambientes isolados para múltiplos clientes em um cluster Kubernetes, cada um com sua própria instância de aplicação integrada com:

- **WhatsApp Business API** - Comunicação automatizada com clientes
- **Google Calendar API** - Gerenciamento de agendamentos
- **Gemini AI** - Processamento inteligente de mensagens
- **ArgoCD** - Deployment contínuo e GitOps

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.11+
- Kubernetes cluster (1.25+)
- ArgoCD instalado
- PostgreSQL e Redis (ou use os manifests incluídos)
- Credenciais das APIs (Google, WhatsApp, Gemini)

### Instalação

1. **Clone o repositório**
```bash
git clone https://github.com/matheushrd/mcp-whats-k8s
cd mcp-platform
```

2. **Instale as dependências do orchestrator**
```bash
pip install -r orchestrator/requirements.txt
```

3. **Configure o banco de dados centralizado**
```bash
kubectl create namespace mcp-platform
kubectl apply -f database/k8s-manifests/
```

4. **Cadastre um novo cliente**
```bash
python scripts/onboarding.py
```

5. **Gere os manifestos do Kubernetes**
```bash
python orchestrator/orchestrator.py
```

6. **Aplique os manifestos**
```bash
cd generated-manifests
./apply-all.sh
```

## 📁 Estrutura do Projeto

```
mcp-platform/
├── orchestrator/          # Script de orquestração e templates
├── mcp-server/           # Aplicação principal (FastAPI)
├── web-ui/               # Interface web para cadastro
├── database/             # Scripts SQL e manifests K8s
├── scripts/              # Utilitários (onboarding)
├── config/               # Configurações e secrets
└── generated-manifests/  # Manifestos gerados (não versionado)
```

## 🔧 Configuração

### config.json

```json
{
  "path_pattern": "/{client_name}/{environment}",
  "clients": [
    {
      "client_name": "comercial-guanabara",
      "environments": {
        "development": true,
        "staging": true,
        "production": false
      },
      "credentials_file": "secrets/comercial-guanabara.env"
    }
  ]
}
```

### Arquivo de Credenciais (.env)

```env
GOOGLE_CALENDAR_ID="seu-calendar-id@group.calendar.google.com"
GOOGLE_PROJECT_ID="seu-projeto"
GOOGLE_CLIENT_EMAIL="service-account@projeto.iam.gserviceaccount.com"
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
GEMINI_API_KEY="sua-api-key-gemini"
WHATSAPP_API_TOKEN="seu-token-whatsapp"
WHATSAPP_PHONE_NUMBER_ID="numero-id"
DATABASE_USER="client_db_user"
DATABASE_PASSWORD="senha-segura"
```

## 🌟 Funcionalidades

### MCP Server

- **Gerenciamento de Agenda**: CRUD completo via Google Calendar
- **Chatbot WhatsApp**: Recebe mensagens e responde usando Gemini AI
- **Segurança**: Escopo restrito da IA apenas para agendamentos
- **Multi-tenant**: Isolamento completo entre clientes

### Orchestrator

- Gera namespaces Kubernetes por ambiente
- Cria secrets com credenciais criptografadas
- Configura deployments com limites de recursos
- Gera Applications do ArgoCD para GitOps

### Web UI

- Interface para cadastro de novos clientes
- Validação de credenciais
- Geração automática de configurações

## 📡 Endpoints da API

### Health Check
```
GET /health
```

### Chat (WhatsApp Integration)
```
POST /api/v1/chat
{
  "message": "Quero agendar um horário",
  "user_id": "5511999999999",
  "send_whatsapp": true
}
```

### Appointments
```
GET /api/v1/appointments/available?date=2024-12-20
POST /api/v1/appointments/create
DELETE /api/v1/appointments/{appointment_id}
```

### Webhook WhatsApp
```
POST /api/v1/webhooks/whatsapp
GET /api/v1/webhooks/whatsapp (verificação)
```

## 🔒 Segurança

- Credenciais armazenadas em Secrets do Kubernetes
- IA com prompts restritos ao escopo de negócio
- Isolamento entre namespaces de clientes
- Autenticação JWT para APIs administrativas

## 📈 Monitoramento

Recomendações:
- Prometheus para métricas
- Grafana para dashboards
- ELK Stack para logs centralizados

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🛠️ Troubleshooting

### Erro ao conectar com Google Calendar
- Verifique se o service account tem permissões no calendário
- Confirme que o GOOGLE_PRIVATE_KEY está formatado corretamente

### WhatsApp não recebe mensagens
- Verifique o webhook URL configurado no Facebook Business
- Confirme que o verify token está correto

### Pod não inicia
- Verifique os logs: `kubectl logs -n <namespace> <pod-name>`
- Confirme que todas as credenciais estão corretas no Secret

## 📞 Suporte

Para suporte, abra uma issue no GitHub ou contate a equipe de desenvolvimento.

## 📋 Visão Geral - k8s

```mermaid
graph TD
    subgraph "Usuários e Atores Externos"
        Admin["👩‍💻 Administrador"]
        EndUser["👤 Cliente Final"]
        Meta["🌐 Meta Platform (WhatsApp API)"]
        GoogleAPI["🌐 Google Cloud (Gemini & Calendar API)"]
    end

    subgraph "Cluster Kubernetes"
        Ingress["🚪 Ingress Controller"]

        subgraph "Namespace: mcp-platform (Serviços Compartilhados)"
            style mcp-platform fill:#e6f0fa,stroke:#b3d1ff
            PostgresDB["🗄️ PostgreSQL"]
            Redis["⚡ Redis"]
            ArgoCD["🔄 ArgoCD"]
            WebUI["🖥️ Web UI (Opcional)"]
            PostgresDB -- "Armazena" --> ConfigClientes("Configuração dos Clientes")
            PostgresDB -- "Armazena" --> Logs("Logs & Agendamentos")
        end

        subgraph "Ambiente Cliente A (Ex: cliente-a-prod)"
            style cliente-a-prod fill:#e8f5e9,stroke:#a5d6a7
            ServiceA["🔧 K8s Service"]
            DeploymentA["🚀 Deployment: MCP Server"]
            SecretA["🔑 K8s Secret (Credenciais Cliente A)"]
            PodA["🤖 Pod: MCP Server (CLIENT_NAME=cliente-a)"]
        end

        subgraph "Ambiente Cliente B (Ex: cliente-b-prod)"
            style cliente-b-prod fill:#e8f5e9,stroke:#a5d6a7
            ServiceB["🔧 K8s Service"]
            DeploymentB["🚀 Deployment: MCP Server"]
            SecretB["🔑 K8s Secret (Credenciais Cliente B)"]
            PodB["🤖 Pod: MCP Server (CLIENT_NAME=cliente-b)"]
        end

        Ingress -- "Rota /api/v1/.../whatsapp/cliente-a" --> ServiceA
        Ingress -- "Rota /api/v1/.../whatsapp/cliente-b" --> ServiceB
        ServiceA --> DeploymentA --> PodA
        ServiceB --> DeploymentB --> PodB
        PodA -- "Usa credenciais" --> SecretA
        PodB -- "Usa credenciais" --> SecretB
        PodA -- "Lê/Escreve dados" --> PostgresDB
        PodA -- "Cache de sessão" --> Redis
        PodB -- "Lê/Escreve dados" --> PostgresDB
        PodB -- "Cache de sessão" --> Redis
    end

    subgraph "Processo de Provisionamento (GitOps)"
        direction LR
        Admin -- "1. Cadastra via UI/CLI" --> WebUI
        WebUI -- "2. Salva no BD Central" --> PostgresDB
        Orchestrator["🐍 Orchestrator Script"] -- "3. Lê config do BD" --> PostgresDB
        Orchestrator -- "4. Gera Manifestos YAML" --> GitRepo["📂 Git Repo (Manifestos K8s)"]
        ArgoCD -- "5. Sincroniza (Pull)" --> GitRepo
        ArgoCD -- "6. Aplica no Cluster" --> DeploymentA
        ArgoCD -- " " --> DeploymentB
    end

    EndUser -- "WhatsApp Msg" --> Meta
    Meta -- "Webhook" --> Ingress
    PodA -- "API Calls" --> GoogleAPI
    PodB -- "API Calls" --> GoogleAPI
    PodA -- "Envia Resposta" --> Meta
    PodB -- "Envia Resposta" --> Meta
```

## 📋 Visão Geral - DEVELOPMENT

```mermaid
graph TD
    subgraph "Ambiente Local do Desenvolvedor"
        Dev["👨‍💻 Desenvolvedor"]
        Code["📁 Código Fonte (Local)"]
        EnvFile["📄 .env file"]
        InitSQL["📄 database/init.sql"]
    end

    subgraph "Docker Engine"
        subgraph RedeDockerCompose ["Rede Docker Compose"]
            style RedeDockerCompose fill:#e0f2f1,stroke:#80cbc4
            
            WebApp["🌐 web-ui <br> localhost:3000"]
            APIServer["⚙️ mcp-server <br> localhost:8000"]
            Postgres["🗄️ postgres <br> localhost:5432"]
            Redis["⚡ redis <br> localhost:6379"]

            WebApp -- "API Request" --> APIServer
            APIServer -- "Conexão DB" --> Postgres
            APIServer -- "Conexão Cache" --> Redis
        end
    end
    
    subgraph "Volumes Docker (Dados Persistentes)"
        PostgresData["🗄️ postgres_data"]
        RedisData["⚡ redis_data"]
    end

    Dev -- "1. Executa 'docker compose up'" --> Docker
    Dev -- "2. Acessa no navegador" --> WebApp
    Dev -- "3. Testa API" --> APIServer
    
    Code -- "Volume Mount (Hot-Reload)" --> APIServer
    EnvFile -- "Carrega variáveis de ambiente" --> APIServer
    InitSQL -- "Inicializa o schema" --> Postgres

    Postgres -- "Grava/Lê dados" --> PostgresData
    Redis -- "Grava/Lê dados" --> RedisData

    subgraph "APIs Externas"
        GoogleAPI["🌐 Google Cloud APIs"]
        MetaAPI["🌐 Meta (WhatsApp) API"]
    end

    APIServer -- "Chamadas HTTP" --> GoogleAPI
    APIServer -- "Chamadas HTTP" --> MetaAPI
```