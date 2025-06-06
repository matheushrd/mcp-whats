from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import asyncio
import logging
from app.config import settings
from app.utils.routers import appointments, webhooks, onboarding_api
from app.utils.services import calendar_service, whatsapp_service, gemini_service
import redis.asyncio as aioredis

# Configura o logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Segurança
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Incialização da aplicação
    logger.info(f"Iniciando MCP Server para {settings.CLIENT_NAME} - {settings.ENVIRONMENT}")

    # **CORREÇÃO**: Disponibiliza as configurações no estado da aplicação
    app.state.settings = settings

    # Conexão com o Redis
    redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
    logger.info(f"Conectando ao Redis em {redis_url}")
    try:
        app.state.redis = aioredis.Redis.from_url(redis_url)
        await app.state.redis.ping()
        logger.info("Conectado ao Redis com sucesso.")
    except Exception as e:
        logger.error(f"Falha ao conectar ao Redis: {e}")
        app.state.redis = None

    # Inicialização dos serviços
    app.state.calendar_service = calendar_service.CalendarService()
    app.state.whatsapp_service = whatsapp_service.WhatsAppService()
    app.state.gemini_service = gemini_service.GeminiService()
    logger.info("Serviços principais inicializados.")

    yield

    # Encerramento da aplicação
    if app.state.redis:
        await app.state.redis.close()
        logger.info("Conexão com o Redis fechada.")
    logger.info("Servidor MCP encerrado.")

app = FastAPI(
    title="MCP Server",
    description="Servidor da Multi-Client Platform para gerenciamento de agendamentos",
    version="1.0.0",
    lifespan=lifespan
)

# Inclusão das rotas da API
app.include_router(appointments.router, prefix="/api/v1/appointments", tags=["Appointments"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])
app.include_router(onboarding_api.router, prefix="/api/v1", tags=["Client Onboarding"])

@app.get("/")
async def root():
    return {
        "service": "MCP Server",
        "client": settings.CLIENT_NAME,
        "environment": settings.ENVIRONMENT,
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    redis_status = "desconectado"
    if hasattr(app.state, 'redis') and app.state.redis:
        try:
            await app.state.redis.ping()
            redis_status = "conectado"
        except Exception as e:
            logger.error(f"Ping do Redis falhou no health check: {e}")
            redis_status = "não saudável"
    
    calendar_status = "desconhecido"
    if hasattr(app.state, 'calendar_service') and app.state.calendar_service:
        try:
            calendar_status = await app.state.calendar_service.health_check()
        except Exception as e:
            logger.error(f"Health check do serviço de calendário falhou: {e}")
            calendar_status = "não saudável"
    
    overall_status = "não saudável"
    if redis_status == "conectado" and calendar_status == "healthy":
        overall_status = "saudável"
    
    return {
        "status": overall_status,
        "services": {
            "redis": redis_status,
            "calendar": calendar_status
        }
    }

@app.post("/api/v1/chat")
async def chat_endpoint(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        body = await request.json()
        user_message = body.get("message", "")
        user_id = body.get("user_id", "")

        ai_response = await app.state.gemini_service.process_message(
            user_message=user_message,
            user_id=user_id,
            context={
                "client_name": settings.CLIENT_NAME,
                "calendar_service": app.state.calendar_service
            }
        )

        if body.get("send_whatsapp", False):
            whatsapp_number = body.get("whatsapp_number")
            if not whatsapp_number:
                raise HTTPException(status_code=400, detail="whatsapp_number é obrigatório quando send_whatsapp é true.")
            await app.state.whatsapp_service.send_message(
                to=whatsapp_number,
                message=ai_response
            )

        return {
            "response": ai_response,
            "user_id": user_id,
            "processed": True
        }
    except Exception as e:
        logger.error(f"Erro no processamento do chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao processar mensagem: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)