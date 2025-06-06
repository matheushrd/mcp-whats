#!/bin/bash

# MCP Platform - Setup Completo
# Este script configura e executa todo o projeto

set -e  # Para se houver erro

echo "🚀 MCP Platform - Setup Completo"
echo "================================"

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para verificar comandos
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 não está instalado${NC}"
        exit 1
    fi
}

# 1. Verificar pré-requisitos
echo -e "\n${YELLOW}📋 Verificando pré-requisitos...${NC}"
check_command docker
check_command docker compose
check_command python3
check_command pip3
check_command kubectl

# 2. Criar estrutura de diretórios
echo -e "\n${YELLOW}📁 Criando estrutura de diretórios...${NC}"
mkdir -p config/secrets
mkdir -p logs
mkdir -p generated-manifests

# 3. Configurar arquivo de credenciais
echo -e "\n${YELLOW}🔐 Configurando credenciais...${NC}"
if [ ! -f "config/secrets/comercial-guanabara.env" ]; then
    echo "Criando arquivo de credenciais..."
    cp config/secrets/comercial-guanabara.env config/secrets/comercial-guanabara.env 2>/dev/null || true
fi

# 4. Instalar dependências Python
echo -e "\n${YELLOW}📦 Instalando dependências Python...${NC}"
pip3 install -r orchestrator/requirements.txt
pip3 install -r mcp-server/requirements.txt
pip3 install -r scripts/requirements.txt

# 5. Escolher modo de execução
echo -e "\n${YELLOW}🤔 Como você deseja executar o projeto?${NC}"
echo "1) Desenvolvimento Local (Docker Compose)"
echo "2) Kubernetes (Produção)"
echo "3) Apenas gerar manifestos Kubernetes"
read -p "Escolha uma opção (1-3): " choice

case $choice in
    1)
        echo -e "\n${GREEN}🐳 Iniciando em modo Desenvolvimento Local...${NC}"
        
        # Copiar .env se não existir
        if [ ! -f ".env" ]; then
            cp .env .env
            echo -e "${YELLOW}⚠️  Arquivo .env criado. Por favor, edite com suas credenciais!${NC}"
            echo "Abra o arquivo .env e adicione:"
            echo "- GEMINI_API_KEY"
            echo "- Ajuste outras configurações se necessário"
            read -p "Pressione ENTER depois de configurar o .env..."
        fi
        
        # Build das imagens
        echo -e "\n${YELLOW}🔨 Building Docker images...${NC}"
        docker compose build
        
        # Iniciar serviços
        echo -e "\n${YELLOW}🚀 Iniciando serviços...${NC}"
        docker compose up -d
        
        # Aguardar serviços iniciarem
        echo -e "\n${YELLOW}⏳ Aguardando serviços iniciarem...${NC}"
        sleep 10
        
        # Verificar status
        docker compose ps
        
        echo -e "\n${GREEN}✅ Projeto rodando em modo desenvolvimento!${NC}"
        echo -e "\n📍 URLs disponíveis:"
        echo "- MCP Server: http://localhost:8000"
        echo "- Web UI: http://localhost:3000"
        echo "- PostgreSQL: localhost:5432"
        echo "- Redis: localhost:6379"
        echo -e "\n📝 Comandos úteis:"
        echo "- Ver logs: docker compose logs -f"
        echo "- Parar: docker compose down"
        echo "- Reiniciar: docker compose restart"
        ;;
        
    2)
        echo -e "\n${GREEN}☸️  Iniciando em modo Kubernetes...${NC}"
        
        # Verificar cluster
        echo -e "\n${YELLOW}🔍 Verificando cluster Kubernetes...${NC}"
        kubectl cluster-info
        
        # Criar namespace
        echo -e "\n${YELLOW}📦 Criando namespace...${NC}"
        kubectl create namespace mcp-platform --dry-run=client -o yaml | kubectl apply -f -
        
        # Aplicar banco de dados
        echo -e "\n${YELLOW}🗄️  Configurando banco de dados...${NC}"
        kubectl apply -f database/k8s-manifests/
        
        # Aguardar PostgreSQL
        echo -e "\n${YELLOW}⏳ Aguardando PostgreSQL iniciar...${NC}"
        kubectl wait --for=condition=ready pod -l app=postgres -n mcp-platform --timeout=120s
        
        # Build e push das imagens
        echo -e "\n${YELLOW}🔨 Build das imagens Docker...${NC}"
        read -p "Digite o registry Docker (ex: docker.io/seuusuario): " REGISTRY
        
        docker build -t $REGISTRY/mcp-server:latest mcp-server/
        docker build -t $REGISTRY/mcp-web-ui:latest web-ui/
        
        echo -e "\n${YELLOW}📤 Push das imagens...${NC}"
        docker push $REGISTRY/mcp-server:latest
        docker push $REGISTRY/mcp-web-ui:latest
        
        # Atualizar registry nos templates
        sed -i "s|your-registry|$REGISTRY|g" orchestrator/templates/deployment.yaml.j2
        
        # Gerar manifestos
        echo -e "\n${YELLOW}📝 Gerando manifestos Kubernetes...${NC}"
        python3 orchestrator/orchestrator.py
        
        # Aplicar manifestos
        echo -e "\n${YELLOW}🚀 Aplicando manifestos...${NC}"
        cd generated-manifests && ./apply-all.sh && cd ..
        
        # Verificar pods
        echo -e "\n${YELLOW}🔍 Verificando pods...${NC}"
        kubectl get pods --all-namespaces | grep -E "(mcp-|barbearia)"
        
        echo -e "\n${GREEN}✅ Projeto implantado no Kubernetes!${NC}"
        echo -e "\n📝 Próximos passos:"
        echo "1. Configure o Ingress para expor os serviços"
        echo "2. Configure o webhook do WhatsApp"
        echo "3. Monitore os logs: kubectl logs -n <namespace> -l app=mcp-server"
        ;;
        
    3)
        echo -e "\n${GREEN}📄 Gerando apenas manifestos...${NC}"
        
        # Verificar config.json
        if [ ! -f "config/config.json" ]; then
            echo -e "${RED}❌ config/config.json não encontrado${NC}"
            echo "Execute primeiro: python3 scripts/onboarding.py"
            exit 1
        fi
        
        # Gerar manifestos
        python3 orchestrator/orchestrator.py
        
        echo -e "\n${GREEN}✅ Manifestos gerados em: generated-manifests/${NC}"
        echo "Para aplicar: cd generated-manifests && ./apply-all.sh"
        ;;
        
    *)
        echo -e "${RED}❌ Opção inválida${NC}"
        exit 1
        ;;
esac

# Testes finais
echo -e "\n${YELLOW}🧪 Executando testes de conectividade...${NC}"

if [ "$choice" == "1" ]; then
    # Testar health check local
    sleep 5
    echo -e "\n${YELLOW}🏥 Testando health check...${NC}"
    curl -s http://localhost:8000/health | python3 -m json.tool || echo -e "${RED}❌ Health check falhou${NC}"
fi

# Instruções finais
echo -e "\n${GREEN}🎉 Setup concluído!${NC}"
echo -e "\n${YELLOW}📋 Checklist final:${NC}"
echo "[ ] Adicione a chave do Gemini AI no arquivo .env ou secrets"
echo "[ ] Compartilhe o Google Calendar com: mcp-calendar-service@minimalroutesproject.iam.gserviceaccount.com"
echo "[ ] Configure o webhook do WhatsApp no Facebook Business"
echo "[ ] Teste o envio de mensagens WhatsApp"

echo -e "\n${YELLOW}📚 Documentação:${NC}"
echo "- README.md: Visão geral do projeto"
echo "- DEPLOYMENT.md: Guia detalhado de deployment"

echo -e "\n${GREEN}Happy coding! 🚀${NC}"