from fastapi import APIRouter, HTTPException, Body, Depends, Request
from app.models import ClientOnboardData, OnboardResponse
from pathlib import Path
import json
import re
from datetime import datetime
import logging
import asyncpg

logger = logging.getLogger(__name__)

SECRETS_DIR_PATH = Path("/config_data/secrets")

router = APIRouter()

async def get_db_connection(request: Request):
    # Acessa a conexão Redis do estado do app para obter as configs do DB
    # Esta é uma maneira de obter acesso às configurações de forma centralizada.
    # Em um projeto maior, você usaria um pool de conexões injetado.
    app_state = request.app.state
    settings = app_state.settings # Supondo que as settings estão no estado

    return await asyncpg.connect(
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD,
        database=settings.DATABASE_NAME,
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT
    )

def save_credentials_api(client_name: str, credentials_dict: dict):
    """Salva as credenciais do cliente em um arquivo .env (função mantida)."""
    try:
        SECRETS_DIR_PATH.mkdir(parents=True, exist_ok=True)
        credentials_file = SECRETS_DIR_PATH / f"{client_name}.env"
        with open(credentials_file, 'w', encoding='utf-8') as f:
            for key, value in credentials_dict.items():
                processed_value = str(value if value is not None else "")
                escaped_value = processed_value.replace('"', '\\"').replace('\n', '\\n')
                f.write(f'{key.upper()}="{escaped_value}"\n')
        logger.info(f"Credenciais salvas para {client_name} em: {credentials_file}")
        return f"secrets/{client_name}.env"
    except IOError as e:
        logger.error(f"Erro de I/O ao salvar arquivo de credenciais para {client_name}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao salvar arquivo de credenciais.")


@router.post("/onboard-client", response_model=OnboardResponse, tags=["Client Onboarding"])
async def onboard_client_endpoint(
    request: Request,
    payload: ClientOnboardData = Body(...)
):
    """
    Endpoint para registrar (onboard) um novo cliente na plataforma, salvando no banco de dados.
    """
    logger.info(f"Recebida requisição de onboarding para o cliente: {payload.client_name}")
    
    # Validação do nome do cliente (regex)
    pattern = r'^[a-z0-9-]+$'
    if not re.match(pattern, payload.client_name):
        raise HTTPException(status_code=400, detail="Nome do cliente deve conter apenas letras minúsculas, números e hífens.")

    conn = await get_db_connection(request)
    
    try:
        # 1. Verificar se o cliente já existe
        existing_client = await conn.fetchrow("SELECT client_name FROM clients WHERE client_name = $1", payload.client_name)
        if existing_client:
            raise HTTPException(status_code=400, detail=f"Cliente '{payload.client_name}' já existe.")

        # 2. Salvar as credenciais em um arquivo .env
        relative_credentials_file_path = save_credentials_api(payload.client_name, payload.credentials.dict())
        
        # 3. Inserir o novo cliente no banco de dados
        await conn.execute(
            """
            INSERT INTO clients (client_name, business_name, business_type, environments, credentials_file)
            VALUES ($1, $2, $3, $4, $5)
            """,
            payload.client_name,
            payload.business_name,
            payload.business_type.value,
            json.dumps(payload.environments.dict()), # Converte dict para string JSON
            relative_credentials_file_path
        )
        
        logger.info(f"Cliente '{payload.client_name}' registrado com sucesso no banco de dados.")
        
        return OnboardResponse(
            message=f"Cliente '{payload.client_name}' registrado com sucesso!",
            client_name=payload.client_name
        )
    except asyncpg.exceptions.UniqueViolationError:
         raise HTTPException(status_code=400, detail=f"Cliente '{payload.client_name}' já existe (conflito no banco de dados).")
    except Exception as e:
        logger.error(f"Erro inesperado durante o onboarding de {payload.client_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno inesperado ao processar o cadastro.")
    finally:
        await conn.close()