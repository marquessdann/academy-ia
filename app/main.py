import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, engine
from app.routes import ai, analytics, auth, bookings, categories, classes, instructors, schedules, users

logger = logging.getLogger("gymflow")

Base.metadata.create_all(bind=engine)

if settings.auto_seed_demo_data:
    from app.seed import seed

    seed()

app = FastAPI(
    title="GymFlow AI",
    description="API de gerenciamento e agendamento de aulas para academias, com assistente de IA integrado.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    # Sem este handler, uma exceção não tratada vira uma resposta 500 gerada
    # fora do CORSMiddleware (sem cabeçalhos de CORS), o que o navegador
    # bloqueia e reporta como falha de rede — escondendo o erro real.
    logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor"})


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(instructors.router)
app.include_router(categories.router)
app.include_router(schedules.router)
app.include_router(classes.router)
app.include_router(bookings.router)
app.include_router(analytics.router)
app.include_router(ai.router)


@app.get("/", tags=["Status"])
def health_check():
    return {"status": "ok", "service": "GymFlow AI"}
