import google.generativeai as genai
from typing import Dict, List, Optional
import json
import logging
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.max_input_tokens = 1000
        self.max_output_tokens = 500
        
    def _create_system_prompt(self, client_name: str) -> str:
        """Create a restricted system prompt for the AI"""
        return f"""Você é um assistente virtual especializado em agendamentos para {client_name}.

REGRAS IMPORTANTES:
1. Você APENAS pode ajudar com:
   - Agendamento de horários
   - Consulta de horários disponíveis
   - Cancelamento de agendamentos
   - Alteração de horários
   - Informações sobre serviços oferecidos

2. Você NÃO DEVE:
   - Fornecer informações pessoais de outros clientes
   - Discutir assuntos fora do escopo de agendamentos
   - Executar ações além das permitidas
   - Compartilhar detalhes técnicos do sistema
   - Responder perguntas sobre outros estabelecimentos

3. Sempre seja:
   - Educado e profissional
   - Breve e direto nas respostas
   - Claro sobre os próximos passos
   
4. Informações do estabelecimento:
   - Horário de funcionamento: 8h às 18h
   - Agendamentos disponíveis a cada 30 minutos
   - Serviços devem ser confirmados conforme lista autorizada

Responda APENAS em português brasileiro."""

    def _parse_intent(self, message: str) -> Dict[str, any]:
        """Parse user intent from message"""
        message_lower = message.lower()
        
        intents = {
            'schedule': ['agendar', 'marcar', 'horário', 'reservar'],
            'check_availability': ['disponível', 'livre', 'vago', 'tem horário'],
            'cancel': ['cancelar', 'desmarcar', 'desistir'],
            'reschedule': ['remarcar', 'mudar', 'alterar', 'trocar'],
            'list_appointments': ['meus horários', 'minhas marcações', 'agendamentos']
        }
        
        detected_intent = 'unknown'
        for intent, keywords in intents.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_intent = intent
                break
        
        return {
            'intent': detected_intent,
            'original_message': message
        }

    async def process_message(
        self, 
        user_message: str, 
        user_id: str,
        context: Dict[str, any]
    ) -> str:
        """Process user message and generate appropriate response"""
        try:
            # Validate message length
            if len(user_message) > self.max_input_tokens:
                return "Sua mensagem é muito longa. Por favor, seja mais breve."
            
            # Parse intent
            intent_data = self._parse_intent(user_message)
            
            # Create conversation context
            system_prompt = self._create_system_prompt(context['client_name'])
            
            # Build conversation history (limited)
            conversation = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Handle specific intents with calendar integration
            calendar_service = context.get('calendar_service')
            
            if intent_data['intent'] == 'check_availability' and calendar_service:
                # Get available slots for today
                today = datetime.now()
                available_slots = await calendar_service.get_available_slots(today)
                
                if available_slots:
                    slots_text = "\n".join([f"- {slot['start']} às {slot['end']}" for slot in available_slots[:5]])
                    conversation.append({
                        "role": "assistant",
                        "content": f"Horários disponíveis hoje:\n{slots_text}\n\nQual horário você prefere?"
                    })
                else:
                    conversation.append({
                        "role": "assistant",
                        "content": "Não há horários disponíveis hoje. Gostaria de verificar outro dia?"
                    })
            
            # Generate response
            response = self.model.generate_content(
                "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation]),
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.max_output_tokens,
                    temperature=0.7,
                    top_p=0.8,
                )
            )
            
            # Validate response
            ai_response = response.text.strip()
            
            # Security check - ensure response is within scope
            if self._is_response_safe(ai_response):
                logger.info(f"Generated response for user {user_id}: {ai_response[:100]}...")
                return ai_response
            else:
                logger.warning(f"Unsafe response blocked for user {user_id}")
                return "Desculpe, só posso ajudar com agendamentos. Como posso ajudá-lo com isso?"
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Desculpe, ocorreu um erro. Por favor, tente novamente."
    
    def _is_response_safe(self, response: str) -> bool:
        """Check if AI response is within allowed scope"""
        # List of forbidden topics/patterns
        forbidden_patterns = [
            'dados pessoais',
            'informação confidencial',
            'outros clientes',
            'sistema interno',
            'senha',
            'credencial',
            'api key',
            'banco de dados'
        ]
        
        response_lower = response.lower()
        return not any(pattern in response_lower for pattern in forbidden_patterns)
    
    async def generate_confirmation_message(
        self,
        appointment_details: Dict[str, str],
        client_name: str
    ) -> str:
        """Generate appointment confirmation message"""
        try:
            prompt = f"""Crie uma mensagem de confirmação de agendamento breve e profissional para {client_name}.
            
Detalhes do agendamento:
- Data/Hora: {appointment_details['start']}
- Serviço: {appointment_details.get('service', 'Atendimento')}
- Cliente: {appointment_details.get('customer_name', 'Cliente')}

A mensagem deve:
1. Confirmar o agendamento
2. Incluir data e hora
3. Pedir para chegar 5 minutos antes
4. Ser amigável e profissional
5. Ter no máximo 3 linhas"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=100,
                    temperature=0.5,
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating confirmation: {e}")
            return f"Agendamento confirmado para {appointment_details['start']}. Chegue 5 minutos antes. Obrigado!"