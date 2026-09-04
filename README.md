# 🏋️ GymFlow AI

Sistema de gerenciamento e agendamento de aulas para academias, com um
assistente de IA que consulta dados reais da aplicação para responder
perguntas sobre vagas, horários e reservas.

Projeto de portfólio construído para demonstrar, na prática, habilidades de
backend com Python: API REST, banco de dados relacional, autenticação,
regras de negócio de agendamento e integração com LLMs via function calling.

> 💡 **Sobre este projeto**: o objetivo não é ser uma arquitetura complexa ou
> "enterprise", e sim mostrar código limpo, organizado e funcional — do jeito
> que um bom desenvolvedor backend júnior entregaria uma feature real.

---

## 📌 Qual problema o projeto resolve

Academias que gerenciam aulas em grade fixa (musculação, funcional, spinning,
yoga...) normalmente lidam com dois problemas manuais:

1. **Agendamento**: alunos reservam vaga em aulas por WhatsApp, papel ou
   planilha, o que gera overbooking, reservas duplicadas e falta de controle
   de vagas em tempo real.
2. **Visibilidade de dados**: a academia tem dados de ocupação, mas raramente
   os usa para responder perguntas simples como *"qual o horário mais vazio
   de funcional?"* ou para ajudar o próprio aluno a decidir quando treinar.

O GymFlow AI resolve os dois problemas: um sistema de agendamento com
controle automático de vagas, e um assistente de IA que transforma os dados
já existentes no banco em respostas úteis, sem depender de relatórios
manuais.

---

## 🔁 Como funciona o sistema de agendamento

- Cada **modalidade** (`Category`) — musculação, funcional, spinning, yoga —
  pode ter uma **grade horária recorrente** (`GymSchedule`), por exemplo
  "Funcional toda terça às 19h, com o professor Bruno, capacidade 15".
- A partir dessa grade (ou de forma avulsa), o admin cria **aulas concretas**
  (`GymClass`): uma instância com data/hora de início e fim e um limite de
  vagas (`capacity`).
- Um aluno autenticado reserva uma vaga em `POST /bookings`. O
  `booking_service` aplica as regras de negócio antes de confirmar:
  - ❌ não permite reservar uma aula que já passou;
  - ❌ não permite duas reservas ativas do mesmo aluno na mesma aula
    (reserva duplicada);
  - ❌ não permite reservar se a aula já atingiu a capacidade máxima
    (conta apenas reservas com status `confirmed`);
  - ✅ caso contrário, cria a reserva com status `confirmed`.
- Cancelar uma reserva (`DELETE /bookings/{id}`) apenas muda o status para
  `cancelled` (soft cancel, mantém histórico) e libera a vaga automaticamente,
  já que a contagem de ocupação sempre filtra por `status = confirmed`.
- O aluno pode listar suas próximas aulas e seu histórico completo em
  `GET /users/me/bookings`.

---

## 🤖 Como a IA acessa informações do sistema

O assistente **não** responde de forma genérica nem "alucina" dados. Ele
funciona com uma camada de **tools (function calling)**, em
[`app/ai/tools.py`](app/ai/tools.py): um conjunto fixo de funções Python que
consultam o banco de dados de forma controlada.

```
get_available_classes(category, date, period)   → aulas futuras com vaga
get_classes_by_period(category, date, period)    → todas as aulas de um filtro
get_user_bookings(user_id, only_upcoming)         → reservas do aluno logado
get_class_occupancy(class_id)                     → vagas ocupadas/disponíveis
get_quietest_times(limit)                         → horários com menor ocupação média
```

O fluxo em [`app/ai/chat_service.py`](app/ai/chat_service.py) funciona assim:

1. O aluno manda uma mensagem em `POST /ai/chat` (ex: *"Quais aulas de
   funcional têm vaga amanhã à noite?"*).
2. O `system_prompt` instrui o modelo a **usar apenas as tools disponíveis**
   e nunca inventar aulas, vagas ou horários.
3. O modelo decide qual(is) função(ões) chamar e com quais parâmetros
   (via [function calling da OpenAI](https://platform.openai.com/docs/guides/function-calling)).
4. O backend executa a função real contra o PostgreSQL e devolve o resultado
   ao modelo.
5. O modelo formata uma resposta final em português, baseada exclusivamente
   nesse resultado.

Isso é configurado por `AI_PROVIDER` no `.env`:

- `AI_PROVIDER=openai` → usa a API da OpenAI (function calling real) com a
  chave definida em `OPENAI_API_KEY`. O mesmo padrão de tools funciona com
  qualquer provedor compatível (Claude, Gemini) trocando o cliente em
  `app/ai/client.py`.
- `AI_PROVIDER=mock` (padrão) → um mecanismo local de reconhecimento de
  intenção por palavras-chave decide qual tool chamar, sem precisar de chave
  de API. Isso permite rodar e testar o projeto (inclusive em uma avaliação
  técnica) **sem custo e sem depender de internet**, chamando as mesmas
  funções reais do banco de dados.

Em ambos os casos, a IA nunca executa SQL livre — ela só pode chamar as
funções expostas em `TOOL_REGISTRY`, o que evita respostas inventadas e
mantém o escopo do assistente controlado.

---

## 🧠 Como funciona a recomendação de horários

`app/services/recommendation_service.py` e `analytics_service.py` implementam
uma recomendação **baseada em regras sobre dados reais**, sem Machine
Learning:

1. Cada aula concreta (`GymClass`) tem sua taxa de ocupação calculada:
   `reservas confirmadas / capacidade`.
2. As aulas são agrupadas por **dia da semana + hora** (ex: "terça às 19h"),
   e calcula-se a **ocupação média histórica** de cada slot
   (`get_quietest_slots`).
3. Os slots com menor ocupação média são cruzados com as **aulas futuras**
   que caem nesses mesmos dia/hora, gerando uma recomendação como:

   > "Funcional às 07:00 de quarta-feira — ocupação média histórica de 25%"

Esse mesmo cálculo alimenta a tool `get_quietest_times`, usada pela IA para
responder perguntas como *"qual horário costuma estar mais vazio?"* e *"qual
o melhor horário para eu treinar?"*.

---

## 🛠️ Tecnologias utilizadas

| Camada          | Tecnologia                                             |
|-----------------|---------------------------------------------------------|
| Linguagem       | Python 3.11+                                             |
| Framework web   | FastAPI                                                  |
| Banco de dados  | PostgreSQL (ou Supabase) via SQLAlchemy 2.0              |
| Migrations      | Alembic                                                  |
| Validação       | Pydantic v2                                              |
| Autenticação    | JWT (python-jose) + hash de senha com bcrypt (passlib)   |
| IA              | OpenAI API (function calling), com modo mock local       |
| Testes          | Pytest + SQLite em memória                                |
| Frontend        | HTML, CSS e JavaScript puro (SPA leve, sem framework)     |
| Documentação API| Swagger / OpenAPI (gerado automaticamente pelo FastAPI)  |

---

## 🏗️ Arquitetura

```
app/
├── main.py            # cria a aplicação FastAPI, registra rotas e middlewares
├── config.py           # configurações via variáveis de ambiente (.env)
├── database.py          # engine, sessão e Base do SQLAlchemy
├── seed.py               # popula o banco com dados de demonstração
│
├── models/              # entidades SQLAlchemy (tabelas do banco)
│   ├── user.py, instructor.py, category.py
│   ├── gym_schedule.py, gym_class.py, booking.py
│
├── schemas/             # contratos de entrada/saída da API (Pydantic)
│
├── routes/              # endpoints HTTP (FastAPI routers), finos —
│                          delegam regra de negócio para services/
│
├── services/             # regras de negócio
│   ├── booking_service.py        # reservar/cancelar, valida vagas e duplicidade
│   ├── analytics_service.py      # ocupação por aula e por horário
│   └── recommendation_service.py # recomenda horários menos concorridos
│
├── repositories/          # acesso ao banco (queries SQLAlchemy), isolado das rotas
│
├── auth/                # segurança
│   ├── security.py       # hash/verificação de senha (bcrypt)
│   ├── jwt_handler.py     # geração/validação de JWT
│   └── dependencies.py    # dependências FastAPI: get_current_user / get_current_admin
│
└── ai/                  # assistente de IA
    ├── tools.py           # funções que consultam dados reais (function calling)
    ├── client.py           # cliente da OpenAI
    └── chat_service.py      # orquestra o chat (modo OpenAI real ou mock)
```

A ideia é manter uma separação simples e direta, sem camadas
desnecessárias: **routes** validam e delegam, **services** concentram as
regras de negócio, **repositories** concentram as queries, e **models**
descrevem as tabelas. Nada de microserviços, filas ou padrões avançados —
não é o que o problema pede.

### Modelo de dados

```
User (aluno ou admin) ─┐
                        ├─< Booking >──┐
GymClass ───────────────┘              │
   │  N:1                              │
   ├── Category (modalidade)           │
   ├── Instructor (professor)          │
   └── GymSchedule (grade recorrente, opcional)
```

- `User` tem papel (`role`): `student` ou `admin`.
- `Booking` tem `status`: `confirmed` ou `cancelled`, e uma constraint única
  de `(user_id, class_id)` para reforçar a regra de não duplicidade também
  no nível do banco.
- `GymSchedule` representa o padrão recorrente ("toda terça às 19h") usado
  para gerar aulas; `GymClass` é a instância concreta e reservável.

---

## 🚀 Como executar localmente

### Pré-requisitos
- Python 3.11+
- PostgreSQL (local, Docker ou [Supabase](https://supabase.com)) — ou apenas
  use SQLite para testar rapidamente, sem precisar instalar nada

### 1. Clonar e instalar dependências

```bash
git clone <url-do-repositorio>
cd academy-ia
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com sua string de conexão do PostgreSQL/Supabase e uma
`SECRET_KEY` própria. Para testar rapidamente sem instalar Postgres, basta
usar:

```
DATABASE_URL=sqlite:///./gymflow.db
```

### 3. Rodar as migrations (Postgres) ou criar as tabelas automaticamente

Com Postgres, aplique as migrations do Alembic:

```bash
alembic upgrade head
```

Com SQLite, as tabelas são criadas automaticamente na primeira execução da
API (via `Base.metadata.create_all`).

### 4. (Opcional) Popular com dados de demonstração

```bash
python -m app.seed
```

Cria modalidades, professores, grade horária, aulas dos próximos dias e
usuários de teste:

- **Admin**: `admin@gymflow.com` / `admin123`
- **Aluno**: `ana.paula@example.com` / `aluno123`

### 5. Rodar a API

```bash
uvicorn app.main:app --reload
```

A API sobe em `http://127.0.0.1:8000`. A documentação interativa (Swagger)
fica em **http://127.0.0.1:8000/docs**.

### 6. Rodar o frontend

O frontend é HTML/CSS/JS puro, sem build step. Basta servir a pasta
`frontend/` com qualquer servidor estático:

```bash
cd frontend
python -m http.server 5500
```

Acesse `http://127.0.0.1:5500`. Se a API estiver em outro host/porta, ajuste
`window.GYMFLOW_API_URL` no início de `frontend/js/api.js`.

### 7. Rodar os testes

```bash
pytest
```

Os testes usam SQLite em memória, então não dependem de nenhum banco externo.

---

## 📡 Endpoints principais

| Método | Rota                        | Descrição                                    | Autenticação |
|--------|------------------------------|-----------------------------------------------|--------------|
| POST   | `/auth/register`             | Cria uma conta de aluno                        | -            |
| POST   | `/auth/login`                | Autentica e retorna um JWT                     | -            |
| GET    | `/users/me`                  | Dados do usuário logado                        | JWT          |
| GET    | `/users/me/bookings`         | Reservas do usuário logado                     | JWT          |
| GET    | `/classes`                   | Lista aulas (com filtros e vagas disponíveis)  | -            |
| GET    | `/classes/{id}`              | Detalhe de uma aula                            | -            |
| POST   | `/classes`                   | Cria uma nova aula                             | JWT (admin)  |
| POST   | `/bookings`                  | Reserva uma vaga em uma aula                   | JWT          |
| DELETE | `/bookings/{id}`             | Cancela uma reserva                            | JWT          |
| GET    | `/analytics/occupancy`       | Relatório de ocupação de todas as aulas        | JWT (admin)  |
| GET    | `/analytics/quietest-times`  | Horários com menor ocupação média              | JWT (admin)  |
| GET    | `/analytics/recommendations` | Recomendação de melhores horários              | JWT          |
| POST   | `/ai/chat`                   | Conversa com o assistente de IA                | JWT          |

Endpoints completos, exemplos de payload e schemas de resposta estão
documentados automaticamente em `/docs` (Swagger UI) e `/redoc`.

### Exemplo: reservar uma aula

```bash
curl -X POST http://127.0.0.1:8000/bookings \
  -H "Authorization: Bearer <seu_token_jwt>" \
  -H "Content-Type: application/json" \
  -d '{"class_id": 3}'
```

### Exemplo: conversar com a IA

```bash
curl -X POST http://127.0.0.1:8000/ai/chat \
  -H "Authorization: Bearer <seu_token_jwt>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Quais aulas de funcional têm vaga amanhã à noite?"}'
```

```json
{
  "reply": "Aulas com vagas disponíveis:\n- Funcional com Bruno Lima em 05/09 19:00 — 6 vaga(s) de 15",
  "tools_used": ["get_available_classes"]
}
```

---

## 🔒 Segurança

- Senhas armazenadas com hash **bcrypt** (nunca em texto puro).
- Autenticação via **JWT** (`python-jose`), com expiração configurável.
- Controle de acesso por papel: rotas administrativas usam a dependência
  `get_current_admin`, que bloqueia usuários comuns com `403 Forbidden`.
- Segredos (chave JWT, chave de API de IA, string de conexão do banco) ficam
  **apenas** em variáveis de ambiente (`.env`, listado no `.gitignore`) —
  nunca no código-fonte. `.env.example` documenta as variáveis necessárias
  sem expor valores reais.
- Validação de entrada em todos os endpoints via Pydantic (schemas
  dedicados, com validações como "hora de término deve ser depois da hora de
  início").
- Tratamento de erros consistente: exceções de negócio (aula lotada, reserva
  duplicada, aula não encontrada) retornam códigos HTTP apropriados
  (`400`, `404`, `409`) com mensagens claras.

---

## 🖼️ Screenshots

> Capturas de tela do frontend (login, dashboard do aluno e área
> administrativa). Veja os arquivos em [`docs/screenshots`](docs/screenshots).

| Login | Dashboard do aluno | Chat com IA | Área administrativa |
|-------|---------------------|--------------|------------------------|
| ![login](docs/screenshots/login.png) | ![dashboard](docs/screenshots/dashboard.png) | ![chat](docs/screenshots/chat.png) | ![admin](docs/screenshots/admin.png) |

---

## 🧪 Testes automatizados

O projeto inclui testes com Pytest cobrindo as regras de negócio mais
importantes:

- Cadastro e login (incluindo e-mail duplicado e senha incorreta).
- Controle de acesso (rotas protegidas sem token, rotas admin sem
  privilégio).
- Reserva de aula, **prevenção de reserva duplicada** e **bloqueio quando a
  aula está lotada**.
- Cancelamento de reserva liberando a vaga automaticamente.
- Cálculo de horários menos concorridos e recomendação de horários.

```bash
pytest -v
```

---

## 🔭 Próximas melhorias

- [ ] Notificações por e-mail ao confirmar/cancelar uma reserva.
- [ ] Geração automática de aulas futuras a partir do `GymSchedule` (hoje
      isso é feito no seed; em produção seria um job agendado).
- [ ] Lista de espera automática quando uma aula lotar.
- [ ] Painel de métricas mais completo (retenção de alunos, aulas mais
      procuradas por modalidade/professor).
- [ ] Migrar o frontend para React, caso o projeto cresça em complexidade de
      estado.
- [ ] Suporte a múltiplos provedores de IA configuráveis (OpenAI, Gemini,
      Claude) via variável de ambiente, com o mesmo contrato de tools.
- [ ] Rate limiting no endpoint `/ai/chat` para controle de custo.

---

## 📄 Licença

Projeto de portfólio, livre para uso e estudo.
