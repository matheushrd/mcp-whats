#!/bin/bash

# Quick Start - MCP Platform
# Inicia o projeto rapidamente em modo desenvolvimento

echo "🚀 MCP Platform - Quick Start"
echo "=============================="

# 1. Verificar .env
if [ ! -f ".env" ]; then
    echo "📝 Criando arquivo .env..."
    cat > .env << 'EOF'
# Configurações da Aplicação
CLIENT_NAME=barbearia-do-ze
ENVIRONMENT=development

# Banco de Dados (Docker Compose)
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=mcp_platform
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres

# Google Calendar
GOOGLE_CALENDAR_ID=-
GOOGLE_PROJECT_ID=
GOOGLE_CLIENT_EMAIL=
GOOGLE_PRIVATE_KEY=

# Gemini API
GEMINI_API_KEY=ADICIONE_SUA_CHAVE_AQUI

# WhatsApp Business API
WHATSAPP_API_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_WEBHOOK_VERIFY_TOKEN=

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Segurança
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF
    
    echo "⚠️  IMPORTANTE: Edite o arquivo .env e adicione sua GEMINI_API_KEY!"
    echo "Pressione ENTER para continuar..."
    read
fi

# 2. Instalar dependências (opcional)
read -p "Instalar dependências Python? (s/N): " install_deps
if [[ $install_deps =~ ^[Ss]$ ]]; then
    echo "📦 Instalando dependências..."
    pip3 install -r mcp-server/requirements.txt
fi

# 3. Iniciar com Docker Compose
echo "🐳 Iniciando serviços com Docker Compose..."
docker compose down
docker compose build
docker compose up -d

# 4. Mostrar logs
echo ""
echo "✅ Projeto iniciado!"
echo ""
echo "📍 Serviços disponíveis:"
echo "   - MCP Server: http://localhost:8000"
echo "   - Web UI: http://localhost:3000"
echo "   - Docs API: http://localhost:8000/docs"
echo ""
echo "📝 Comandos úteis:"
echo "   - Ver logs: docker compose logs -f"
echo "   - Parar: docker compose down"
echo "   - Testar API: curl http://localhost:8000/health"
echo ""
echo "⏳ Aguardando serviços iniciarem..."
sleep 10

# 5. Verificar saúde
echo "🏥 Verificando health check..."
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "🎉 Pronto! O MCP Platform está rodando."
echo ""
echo "⚠️  Não esqueça de:"
echo "   1. Adicionar a chave do Gemini no .env"
echo "   2. Compartilhar o calendário Google com a conta de serviço"
echo "   3. Configurar o webhook do WhatsApp"