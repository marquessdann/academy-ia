"""Orquestra o assistente de IA: monta o contexto, chama o modelo (ou o
mecanismo mock) e executa as "tools" que consultam dados reais do sistema.
"""

import json
import unicodedata

from sqlalchemy.orm import Session

from app.ai.client import get_openai_client
from app.ai.tools import TOOL_REGISTRY, TOOL_SCHEMAS
from app.config import settings
from app.models.category import Category
from app.models.user import User
from app.schemas.ai import ChatResponse

SYSTEM_PROMPT = (
    "Você é o assistente virtual da academia GymFlow. Responda sempre em "
    "português, de forma curta e objetiva. Use exclusivamente as funções "
    "(tools) disponíveis para consultar aulas, vagas, reservas e horários "
    "reais do sistema — nunca invente aulas, horários ou vagas. Se não "
    "encontrar dados suficientes, diga isso claramente ao usuário."
)


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def _execute_tool(db: Session, user: User, name: str, args: dict) -> dict | list:
    func = TOOL_REGISTRY[name]
    if name == "get_user_bookings":
        return func(db=db, user_id=user.id, **args)
    return func(db=db, **args)


def get_ai_response(db: Session, user: User, message: str) -> ChatResponse:
    if settings.ai_provider == "openai" and get_openai_client() is not None:
        return _chat_with_openai(db, user, message)
    return _chat_with_mock_engine(db, user, message)


def _chat_with_openai(db: Session, user: User, message: str) -> ChatResponse:
    client = get_openai_client()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]
    tools_used: list[str] = []

    for _ in range(4):
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        choice = response.choices[0].message

        if not choice.tool_calls:
            return ChatResponse(reply=choice.content or "Não consegui gerar uma resposta.", tools_used=tools_used)

        messages.append(
            {
                "role": "assistant",
                "content": choice.content or "",
                "tool_calls": [tc.model_dump() for tc in choice.tool_calls],
            }
        )
        for tool_call in choice.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments or "{}")
            result = _execute_tool(db, user, name, args)
            tools_used.append(name)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, default=str, ensure_ascii=False),
                }
            )

    return ChatResponse(reply="Não consegui concluir a consulta no momento, tente novamente.", tools_used=tools_used)


# ---------------------------------------------------------------------------
# Mecanismo "mock": funciona sem chave de API, usando reconhecimento simples
# de intenção por palavras-chave. Chama exatamente as mesmas tools reais.
# ---------------------------------------------------------------------------

PERIOD_KEYWORDS = {"manha": "morning", "tarde": "afternoon", "noite": "evening"}


def _detect_period(text: str) -> str | None:
    for keyword, period in PERIOD_KEYWORDS.items():
        if keyword in text:
            return period
    return None


def _detect_date(text: str) -> str | None:
    if "amanha" in text:
        return "tomorrow"
    if "hoje" in text:
        return "today"
    return None


def _detect_category(db: Session, text: str) -> str | None:
    categories = db.query(Category).all()
    for category in categories:
        if _strip_accents(category.name.lower()) in text:
            return category.name
    return None


def _chat_with_mock_engine(db: Session, user: User, raw_message: str) -> ChatResponse:
    text = _strip_accents(raw_message.lower())
    category = _detect_category(db, text)
    period = _detect_period(text)
    date = _detect_date(text)

    if "minha" in text and ("reserva" in text or "aula" in text):
        history = "historico" in text or "passad" in text
        args = {"only_upcoming": not history}
        bookings = _execute_tool(db, user, "get_user_bookings", args)
        return ChatResponse(reply=_format_bookings(bookings, history), tools_used=["get_user_bookings"])

    if any(k in text for k in ["vazio", "menos concorrid", "melhor horario", "menor ocupacao", "recomend"]):
        slots = _execute_tool(db, user, "get_quietest_times", {"limit": 3})
        return ChatResponse(reply=_format_quiet_slots(slots), tools_used=["get_quietest_times"])

    if "vaga" in text or "disponivel" in text or "livre" in text:
        args = {"category": category, "date": date, "period": period}
        classes = _execute_tool(db, user, "get_available_classes", args)
        return ChatResponse(reply=_format_available_classes(classes), tools_used=["get_available_classes"])

    if "aula" in text or "modalidade" in text:
        args = {"category": category, "date": date, "period": period}
        classes = _execute_tool(db, user, "get_classes_by_period", args)
        return ChatResponse(reply=_format_classes(classes), tools_used=["get_classes_by_period"])

    return ChatResponse(
        reply=(
            "Posso te ajudar com informações sobre aulas, vagas, suas reservas e "
            "os melhores horários para treinar. Tente perguntar, por exemplo: "
            "'Quais aulas de funcional têm vaga amanhã à noite?' ou "
            "'Quais são minhas próximas aulas?'"
        ),
        tools_used=[],
    )


def _format_available_classes(classes: list[dict]) -> str:
    if not classes:
        return "Não encontrei aulas com vagas disponíveis para esse filtro."
    lines = [
        f"- {c['title']} ({c['category']}) em {c['start_time'][:16].replace('T', ' ')} "
        f"com {c['instructor']} — {c['available_spots']} vaga(s) de {c['capacity']}"
        for c in classes[:8]
    ]
    return "Aulas com vagas disponíveis:\n" + "\n".join(lines)


def _format_classes(classes: list[dict]) -> str:
    if not classes:
        return "Não encontrei aulas cadastradas para esse filtro."
    lines = [
        f"- {c['title']} ({c['category']}) em {c['start_time'][:16].replace('T', ' ')} "
        f"— {c['booked_count']}/{c['capacity']} vagas ocupadas"
        for c in classes[:8]
    ]
    return "Aulas encontradas:\n" + "\n".join(lines)


def _format_bookings(bookings: list[dict], history: bool) -> str:
    if not bookings:
        return "Você não possui reservas históricas." if history else "Você não tem próximas aulas reservadas."
    header = "Seu histórico de reservas:" if history else "Suas próximas aulas:"
    lines = [
        f"- {b['class_title']} ({b['category']}) em {b['start_time'][:16].replace('T', ' ')} — status: {b['status']}"
        for b in bookings[:10]
    ]
    return header + "\n" + "\n".join(lines)


def _format_quiet_slots(slots: list[dict]) -> str:
    if not slots:
        return "Ainda não há dados suficientes de reservas para recomendar um horário."
    lines = [
        f"- {s['day_name']} às {s['hour']}h — ocupação média de {s['average_occupancy_rate'] * 100:.0f}%"
        for s in slots
    ]
    return "Os horários historicamente menos concorridos são:\n" + "\n".join(lines)
