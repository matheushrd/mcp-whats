#!/usr/bin/env python3
"""
MCP Platform - Client Onboarding Script
Interactive CLI tool for registering new clients
"""

import json
import os
import sys
from pathlib import Path
from getpass import getpass
import re
from datetime import datetime

class ClientOnboarding:
    def __init__(self):
        self.config_file = Path("config/config.json")
        self.config = self.load_config()
        
    def load_config(self):
        """Load existing configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # Create default config structure
            return {
                "path_pattern": "/{client_name}/{environment}",
                "argocd": {
                    "namespace": "argocd",
                    "repo_url": "https://github.com/your-org/mcp-manifests.git",
                    "branch": "main"
                },
                "clients": [],
                "database": {
                    "host": "postgres-service.mcp-platform.svc.cluster.local",
                    "port": 5432,
                    "name": "mcp_platform"
                }
            }
    
    def save_config(self):
        """Save configuration to file"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def validate_client_name(self, name):
        """Validate client name format"""
        pattern = r'^[a-z0-9-]+$'
        if not re.match(pattern, name):
            raise ValueError("Nome do cliente deve conter apenas letras minúsculas, números e hífens")
        if name in [client['client_name'] for client in self.config['clients']]:
            raise ValueError("Cliente já existe")
        return True
    
    def get_client_info(self):
        """Get basic client information"""
        print("\n=== Informações do Cliente ===")
        
        while True:
            client_name = input("Nome do cliente (ex: barbearia-do-ze): ").strip().lower()
            try:
                self.validate_client_name(client_name)
                break
            except ValueError as e:
                print(f"❌ Erro: {e}")
        
        business_name = input("Nome do estabelecimento: ").strip()
        business_type = input("Tipo de negócio (barbearia/salão/clínica/spa/mercearia/outro): ").strip()
        
        return {
            "client_name": client_name,
            "business_name": business_name,
            "business_type": business_type
        }
    
    def get_environments(self):
        """Get environment configuration"""
        print("\n=== Ambientes ===")
        print("Quais ambientes deseja criar?")
        
        environments = {}
        env_options = [
            ("development", "Desenvolvimento"),
            ("staging", "Homologação"),
            ("production", "Produção")
        ]
        
        for env_key, env_name in env_options:
            response = input(f"{env_name} (s/n) [s]: ").strip().lower()
            environments[env_key] = response != 'n'
        
        return environments
    
    def get_resources(self):
        """Get resource limits configuration"""
        print("\n=== Recursos ===")
        print("Configurar limites de recursos (deixe em branco para usar padrão)")
        
        resources = {
            "limits": {},
            "requests": {}
        }
        
        # CPU limits
        cpu_limit = input("CPU limit (ex: 500m, 1000m) [500m]: ").strip()
        resources["limits"]["cpu"] = cpu_limit or "500m"
        
        cpu_request = input("CPU request (ex: 250m, 500m) [250m]: ").strip()
        resources["requests"]["cpu"] = cpu_request or "250m"
        
        # Memory limits
        memory_limit = input("Memory limit (ex: 512Mi, 1Gi) [512Mi]: ").strip()
        resources["limits"]["memory"] = memory_limit or "512Mi"
        
        memory_request = input("Memory request (ex: 256Mi, 512Mi) [256Mi]: ").strip()
        resources["requests"]["memory"] = memory_request or "256Mi"
        
        return resources
    
    def get_credentials(self, client_name):
        """Get API credentials"""
        print("\n=== Credenciais das APIs ===")
        print("⚠️  ATENÇÃO: Essas informações são sensíveis e serão armazenadas em arquivo separado")
        
        credentials = {}
        
        # Google Calendar
        print("\n--- Google Calendar ---")
        credentials["GOOGLE_CALENDAR_ID"] = input("Google Calendar ID: ").strip()
        credentials["GOOGLE_PROJECT_ID"] = input("Google Project ID: ").strip()
        credentials["GOOGLE_CLIENT_EMAIL"] = input("Google Client Email: ").strip()
        
        print("Google Private Key (cole a chave completa, pressione Enter duas vezes quando terminar):")
        private_key_lines = []
        while True:
            line = input()
            if not line:
                break
            private_key_lines.append(line)
        credentials["GOOGLE_PRIVATE_KEY"] = '\n'.join(private_key_lines)
        
        # Gemini API
        print("\n--- Gemini API ---")
        credentials["GEMINI_API_KEY"] = getpass("Gemini API Key: ")
        
        # WhatsApp Business API
        print("\n--- WhatsApp Business API ---")
        credentials["WHATSAPP_API_TOKEN"] = getpass("WhatsApp API Token: ")
        credentials["WHATSAPP_PHONE_NUMBER_ID"] = input("WhatsApp Phone Number ID: ").strip()
        credentials["WHATSAPP_WEBHOOK_VERIFY_TOKEN"] = input("Webhook Verify Token [mcp_webhook_verify_token]: ").strip() or "mcp_webhook_verify_token"
        
        # Database
        print("\n--- Database ---")
        credentials["DATABASE_USER"] = input(f"Database User [{client_name}_user]: ").strip() or f"{client_name}_user"
        credentials["DATABASE_PASSWORD"] = getpass("Database Password: ")
        
        return credentials
    
    def save_credentials(self, client_name, credentials):
        """Save credentials to separate file"""
        credentials_dir = Path("config/secrets")
        credentials_dir.mkdir(exist_ok=True)
        
        # Create .gitignore if it doesn't exist
        gitignore_path = credentials_dir / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, 'w') as f:
                f.write("*\n!.gitignore\n")
        
        # Save credentials as .env file
        credentials_file = credentials_dir / f"{client_name}.env"
        with open(credentials_file, 'w') as f:
            for key, value in credentials.items():
                # Escape special characters in values
                escaped_value = value.replace('"', '\\"').replace('\n', '\\n')
                f.write(f'{key}="{escaped_value}"\n')
        
        print(f"✅ Credenciais salvas em: {credentials_file}")
        return f"secrets/{client_name}.env"
    
    def register_client(self):
        """Main registration flow"""
        print("\n🚀 MCP Platform - Cadastro de Novo Cliente")
        print("=" * 50)
        
        try:
            # Get client information
            client_info = self.get_client_info()
            
            # Get environments
            environments = self.get_environments()
            
            # Get resource limits
            resources = self.get_resources()
            
            # Get credentials
            credentials = self.get_credentials(client_info['client_name'])
            
            # Save credentials
            credentials_file = self.save_credentials(client_info['client_name'], credentials)
            
            # Create client configuration
            client_config = {
                "client_name": client_info['client_name'],
                "business_name": client_info['business_name'],
                "business_type": client_info['business_type'],
                "environments": environments,
                "credentials_file": credentials_file,
                "resources": resources,
                "created_at": datetime.now().isoformat()
            }
            
            # Add to configuration
            self.config['clients'].append(client_config)
            
            # Save configuration
            self.save_config()
            
            print("\n✅ Cliente cadastrado com sucesso!")
            print(f"📁 Configuração salva em: {self.config_file}")
            
            # Show next steps
            print("\n📋 Próximos passos:")
            print("1. Execute o orchestrator para gerar os manifestos:")
            print(f"   python orchestrator/orchestrator.py")
            print("2. Aplique os manifestos no Kubernetes:")
            print("   cd generated-manifests && ./apply-all.sh")
            print("3. Configure o webhook do WhatsApp para:")
            print(f"   https://your-domain.com/api/v1/webhooks/whatsapp/{client_info['client_name']}")
            
        except KeyboardInterrupt:
            print("\n\n❌ Cadastro cancelado pelo usuário")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Erro durante o cadastro: {e}")
            sys.exit(1)

def main():
    """Main entry point"""
    onboarding = ClientOnboarding()
    
    while True:
        onboarding.register_client()
        
        print("\n" + "=" * 50)
        another = input("Deseja cadastrar outro cliente? (s/n): ").strip().lower()
        if another != 's':
            break
    
    print("\n👋 Obrigado por usar o MCP Platform!")

if __name__ == '__main__':
    main()