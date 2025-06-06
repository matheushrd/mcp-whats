#!/usr/bin/env python3
"""
MCP Platform Orchestrator
Generates Kubernetes and ArgoCD manifests based on config.json
"""

import json
import os
import sys
import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import argparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPOrchestrator:
    def __init__(self, config_file='config/config.json'):
        self.config = self.load_config(config_file)
        self.template_env = Environment(
            loader=FileSystemLoader('orchestrator/templates'),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.output_dir = Path('generated-manifests')
        
    def load_config(self, config_file):
        """Load and validate configuration file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                logger.info(f"Configuration loaded from {config_file}")
                return config
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)
    
    def create_output_directories(self):
        """Create directory structure for generated manifests"""
        for client in self.config['clients']:
            for env, enabled in client['environments'].items():
                if enabled:
                    client_dir = self.output_dir / client['client_name'] / env
                    client_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created directory: {client_dir}")
    
    def load_credentials(self, credentials_file):
        """Load credentials from environment file"""
        credentials = {}
        try:
            with open(f"config/{credentials_file}", 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        credentials[key] = value.strip('"\'')
            return credentials
        except FileNotFoundError:
            logger.warning(f"Credentials file {credentials_file} not found")
            return {}
    
    def generate_namespace_manifest(self, client_name, environment):
        """Generate Kubernetes namespace manifest"""
        template = self.template_env.get_template('namespace.yaml.j2')
        namespace = f"{client_name}-{environment}"
        
        manifest = template.render(
            namespace=namespace,
            client_name=client_name,
            environment=environment
        )
        
        return manifest
    
    def generate_secret_manifest(self, client, environment):
        """Generate Kubernetes secret manifest with credentials"""
        template = self.template_env.get_template('secret.yaml.j2')
        credentials = self.load_credentials(client['credentials_file'])
        namespace = f"{client['client_name']}-{environment}"
        
        manifest = template.render(
            namespace=namespace,
            client_name=client['client_name'],
            environment=environment,
            credentials=credentials
        )
        
        return manifest
    
    def generate_deployment_manifest(self, client, environment):
        """Generate Kubernetes deployment manifest"""
        template = self.template_env.get_template('deployment.yaml.j2')
        namespace = f"{client['client_name']}-{environment}"
        
        manifest = template.render(
            namespace=namespace,
            client_name=client['client_name'],
            environment=environment,
            resources=client.get('resources', {}),
            database=self.config['database'],
            image_tag=environment if environment != 'production' else 'stable'
        )
        
        return manifest
    
    def generate_service_manifest(self, client, environment):
        """Generate Kubernetes service manifest"""
        template = self.template_env.get_template('service.yaml.j2')
        namespace = f"{client['client_name']}-{environment}"
        
        manifest = template.render(
            namespace=namespace,
            client_name=client['client_name'],
            environment=environment
        )
        
        return manifest
    
    def generate_argocd_application(self, client, environment):
        """Generate ArgoCD Application manifest"""
        template = self.template_env.get_template('argocd-app.yaml.j2')
        namespace = f"{client['client_name']}-{environment}"
        
        manifest = template.render(
            app_name=f"{client['client_name']}-{environment}",
            namespace=namespace,
            client_name=client['client_name'],
            environment=environment,
            repo_url=self.config['argocd']['repo_url'],
            branch=self.config['argocd']['branch'],
            argocd_namespace=self.config['argocd']['namespace']
        )
        
        return manifest
    
    def save_manifest(self, manifest, client_name, environment, manifest_type):
        """Save generated manifest to file"""
        output_path = self.output_dir / client_name / environment / f"{manifest_type}.yaml"
        
        with open(output_path, 'w') as f:
            f.write(manifest)
        
        logger.info(f"Generated {manifest_type} for {client_name}/{environment}")
    
    def generate_all_manifests(self):
        """Generate all manifests for all clients and environments"""
        self.create_output_directories()
        
        for client in self.config['clients']:
            client_name = client['client_name']
            
            for environment, enabled in client['environments'].items():
                if not enabled:
                    continue
                
                # Generate Kubernetes manifests
                namespace_manifest = self.generate_namespace_manifest(client_name, environment)
                self.save_manifest(namespace_manifest, client_name, environment, 'namespace')
                
                secret_manifest = self.generate_secret_manifest(client, environment)
                self.save_manifest(secret_manifest, client_name, environment, 'secret')
                
                deployment_manifest = self.generate_deployment_manifest(client, environment)
                self.save_manifest(deployment_manifest, client_name, environment, 'deployment')
                
                service_manifest = self.generate_service_manifest(client, environment)
                self.save_manifest(service_manifest, client_name, environment, 'service')
                
                # Generate ArgoCD application
                argocd_app = self.generate_argocd_application(client, environment)
                self.save_manifest(argocd_app, client_name, environment, 'argocd-application')
        
        logger.info("All manifests generated successfully!")
        self.generate_apply_script()
    
    def generate_apply_script(self):
        """Generate a shell script to apply all manifests"""
        script_content = """#!/bin/bash
# Apply script for MCP Platform manifests

set -e

echo "Applying MCP Platform manifests..."

# Apply namespaces first
echo "Creating namespaces..."
find generated-manifests -name "namespace.yaml" -exec kubectl apply -f {} \\;

# Apply secrets
echo "Creating secrets..."
find generated-manifests -name "secret.yaml" -exec kubectl apply -f {} \\;

# Apply deployments and services
echo "Creating deployments and services..."
find generated-manifests -name "deployment.yaml" -exec kubectl apply -f {} \\;
find generated-manifests -name "service.yaml" -exec kubectl apply -f {} \\;

# Apply ArgoCD applications
echo "Creating ArgoCD applications..."
find generated-manifests -name "argocd-application.yaml" -exec kubectl apply -f {} \\;

echo "All manifests applied successfully!"
"""
        
        script_path = self.output_dir / 'apply-all.sh'
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o755)
        logger.info(f"Generated apply script: {script_path}")

def main():
    parser = argparse.ArgumentParser(description='MCP Platform Orchestrator')
    parser.add_argument('-c', '--config', default='config/config.json',
                       help='Path to configuration file')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    orchestrator = MCPOrchestrator(args.config)
    orchestrator.generate_all_manifests()

if __name__ == '__main__':
    main()