from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.chat_service import get_ai_response
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.ai import ChatRequest, ChatResponse

router = APIRouter(prefix="/ai", tags=["Assistente IA"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Conversa com o assistente de IA, que consulta dados reais da academia via tools."""
    return get_ai_response(db, current_user, payload.message)
