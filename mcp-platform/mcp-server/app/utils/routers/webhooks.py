from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
import logging
import json
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/whatsapp/{client_name}")
async def verify_client_webhook(
    client_name: str,
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """
    Endpoint de verificação (GET) do webhook do WhatsApp para um cliente específico.
    """
    try:
        from app.main import app
        
        logger.info(f"Recebida tentativa de verificação de webhook para o cliente: {client_name}")

        # A lógica de verificação usa o token global definido no .env
        challenge = app.state.whatsapp_service.verify_webhook(
            mode=hub_mode,
            token=hub_verify_token,
            challenge=hub_challenge
        )
        
        if challenge:
            logger.info(f"Webhook para o cliente '{client_name}' verificado com sucesso.")
            return PlainTextResponse(content=challenge)
        else:
            logger.warning(f"Falha na verificação do webhook para o cliente '{client_name}': Token inválido.")
            raise HTTPException(status_code=403, detail="Verification failed: Token inválido ou modo incorreto.")
            
    except Exception as e:
        logger.error(f"Erro na verificação do webhook para {client_name}: {e}")
        raise HTTPException(status_code=403, detail="Falha na verificação do webhook.")

@router.post("/whatsapp/{client_name}")
async def process_client_webhook(client_name: str, request: Request):
    """
    Endpoint para receber mensagens (POST) do webhook do WhatsApp para um cliente específico.
    """
    # Esta verificação garante que a instância de serviço correta está tratando a requisição.
    if settings.CLIENT_NAME != client_name:
        logger.warning(f"Webhook para o cliente '{client_name}' recebido pela instância errada (esta é para '{settings.CLIENT_NAME}'). Ignorando.")
        raise HTTPException(status_code=404, detail="Cliente não encontrado nesta instância de serviço.")
    
    try:
        from app.main import app
        
        body = await request.json()
        logger.info(f"Recebido webhook para {client_name}: {json.dumps(body, indent=2)}")
        
        parsed_message = app.state.whatsapp_service.parse_webhook_message(body)
        
        if not parsed_message:
            return {"status": "ok"}
        
        await app.state.whatsapp_service.mark_as_read(parsed_message['message_id'])
        
        if parsed_message['type'] == 'text':
            ai_response = await app.state.gemini_service.process_message(
                user_message=parsed_message['text'],
                user_id=parsed_message['from'],
                context={
                    "client_name": client_name,
                    "calendar_service": app.state.calendar_service
                }
            )
            await app.state.whatsapp_service.send_message(
                to=parsed_message['from'],
                message=ai_response
            )
        elif parsed_message['type'] == 'interactive':
            button_id = parsed_message.get('button_id')
            if button_id == 'confirm_appointment':
                response = "Ótimo! Seu horário está confirmado. Até breve!"
            elif button_id == 'cancel_appointment':
                response = "Seu agendamento foi cancelado. Caso queira remarcar, é só me avisar."
            else:
                response = "Opção recebida. Como posso ajudar?"
            await app.state.whatsapp_service.send_message(
                to=parsed_message['from'],
                message=response
            )
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Erro ao processar webhook para {client_name}: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/calendar")
async def calendar_webhook(request: Request):
    """
    Endpoint de webhook do Google Calendar (para notificações push).
    """
    try:
        headers = dict(request.headers)
        logger.info(f"Webhook do calendário recebido: {headers}")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Erro ao processar webhook do calendário: {e}")
        return {"status": "error", "message": str(e)}