# ExpenseFlow — Shared Expense Management Platform

> Production-ready expense sharing with explainable balances, anomaly-detected imports, and a complete audit trail.

## Tech Stack & AI Used

| Layer | Technology |
|---|---|
| **AI Assistants** | **Gemini 3 Flash (Preview)** via GitHub Copilot (Code generation, Architecture, Debugging) |
| Backend | Django 5, Django REST Framework, PostgreSQL |
| Auth | JWT (SimpleJWT) with Refresh Token Rotation |
| Frontend | React 18, TypeScript, Vite, TailwindCSS v3 |
| State | Zustand (auth), React Query (server state) |
| Deployment | Vercel (Frontend & Backend) |

---

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env           # Edit DATABASE_URL, SECRET_KEY, etc.

# Apply migrations and seed demo data
python manage.py migrate
python manage.py seed_data

# Run development server
python manage.py runserver
```

Demo users (all password: `demo1234!`):
- `aisha@example.com` (Admin, Goa Trip 2024)
- `rohan@example.com`
- `priya@example.com`
- `meera@example.com` (left group March 31, 2024)

### Frontend

```bash
cd frontend
npm install
npm run dev       # http://localhost:5173
```

### Run Tests

```bash
cd backend
python -m pytest tests/ -v
# 23/23 tests passing
```

---

## Architecture

```
d:\Mani\
├── backend/
│   ├── apps/
│   │   ├── accounts/       # Custom User model, auth flows
│   │   ├── groups/         # Groups + timeline-aware memberships
│   │   ├── currencies/     # Currency model
│   │   ├── expenses/       # Expenses + 4 split types
│   │   ├── settlements/    # Debt settlements (separate from expenses)
│   │   ├── balances/       # Pure computation (no DB models)
│   │   ├── imports/        # CSV import pipeline + 15 anomaly checks
│   │   ├── audit/          # Append-only audit log
│   │   ├── ai_assist/      # OpenAI integrations (read-only suggestions)
│   │   └── core/           # Base models (UUID, timestamps, soft delete)
│   ├── config/
│   │   ├── settings/       # base, dev, prod, test
│   │   └── urls.py
│   └── tests/
│       ├── test_balance_engine.py
│       └── test_anomaly_detection.py
│
└── frontend/
    └── src/
        ├── api/            # Axios client + all endpoint functions
        ├── pages/          # Auth, Dashboard, Groups, Expenses, Balances,
        │                   # Imports, Settlements, Audit
        ├── store/          # Zustand auth store
        └── types/          # TypeScript type definitions
```

---

## Key Design Decisions

See [DECISIONS.md](./DECISIONS.md) for full rationale.

### 1. Membership Timeline Enforcement
Every expense is validated against `GroupMembership.joined_at` / `left_at`. A member cannot be assigned expenses outside their active period. This is enforced at both the serializer level and in the Balance Engine.

### 2. Balance Engine
- No balances are stored in the database — all computed on-demand.
- **Zero-sum invariant**: sum of all net balances always equals 0.
- **Debt minimization**: O(n log n) greedy two-heap algorithm.
- **Explainability**: every peso of every balance is traced to a specific expense or settlement.

### 3. Import Pipeline
- Original files are **never modified**.
- 15 anomaly types, each requiring explicit user approval.
- Two-phase: detect first, then execute only approved rows.
- Full downloadable report after import.

### 4. AI Assist
- Read-only suggestions only — AI never modifies data.
- Every AI suggestion includes a disclaimer.
- Graceful fallback (template-based) if OpenAI key not configured.

### 5. Audit Log
- Append-only model (`AuditLog`).
- Captures: actor, action, resource, before/after state, IP, user agent.
- Never deleted, never modified.

---

## Environment Variables

### Backend (`.env`)

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgresql://user:password@host:5432/dbname
ALLOWED_HOSTS=localhost,127.0.0.1

# Email (console backend for dev)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# OpenAI (optional — AI degrades gracefully without it)
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Frontend URL (for CORS and email links)
FRONTEND_URL=http://localhost:5173
```

### Frontend (`.env.development`)

```env
VITE_API_URL=http://localhost:8000/api
```

---

## API Reference

Base URL: `http://localhost:8000/api/`

Interactive API docs: `http://localhost:8000/api/schema/swagger/`

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register/` | Register new user |
| POST | `/auth/login/` | Get JWT tokens |
| POST | `/auth/logout/` | Blacklist refresh token |
| POST | `/auth/token/refresh/` | Rotate access token |
| GET | `/auth/me/` | Current user profile |

### Groups
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/groups/` | List / create groups |
| GET/PATCH/DELETE | `/groups/{id}/` | Group detail |
| GET | `/groups/{id}/members/` | List memberships |
| POST | `/groups/{id}/members/add/` | Add member |
| POST | `/groups/{id}/members/leave/` | Leave group |

### Expenses
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/expenses/groups/{id}/` | List / create expenses |
| GET/PATCH/DELETE | `/expenses/{id}/` | Expense detail |

### Balances
| Method | Endpoint | Description |
|---|---|---|
| GET | `/balances/groups/{id}/` | Net balances for all members |
| GET | `/balances/groups/{id}/simplified/` | Minimal settlement transactions |
| GET | `/balances/groups/{id}/explain/?user_id=` | Full explainable breakdown |

### Imports
| Method | Endpoint | Description |
|---|---|---|
| POST | `/imports/upload/` | Upload CSV |
| GET | `/imports/{id}/` | Import job status |
| GET | `/imports/{id}/anomalies/` | List anomalies |
| POST | `/imports/{id}/anomalies/{id}/resolve/` | Approve/reject anomaly |
| POST | `/imports/{id}/execute/` | Execute approved import |
| GET | `/imports/{id}/report/` | Download CSV report |

---

## Deployment

### Railway (Backend)
1. Create Railway project
2. Add PostgreSQL service
3. Set environment variables (DATABASE_URL, SECRET_KEY, etc.)
4. Connect GitHub repo, set root to `backend/`
5. Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

### Vercel (Frontend)
1. Import GitHub repo
2. Set root to `frontend/`
3. Set `VITE_API_URL` environment variable
4. Vercel auto-detects Vite, deploys automatically

### Neon (PostgreSQL)
1. Create Neon project
2. Copy `DATABASE_URL` to Railway env vars
3. Run `python manage.py migrate` via Railway shell
