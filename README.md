<div align="center">

# 🚀 LaunchKit

### Production-grade B2B SaaS Starter Template

**Auth · Organizations · RBAC · Stripe Billing · Usage Metering · Admin Panel · AI Feature**

Built with FastAPI + PostgreSQL + React — the foundation under every client MVP.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql)](https://postgresql.org)
[![Stripe](https://img.shields.io/badge/Stripe-Billing-635BFF?style=flat-square&logo=stripe)](https://stripe.com)
[![License](https://img.shields.io/badge/License-MIT-00C896?style=flat-square)](LICENSE)

</div>

---

## 📸 Screenshots

<div align="center">

| Login | Dashboard |
|-------|-----------|
| ![Login](docs/screenshots/login.png) | ![Dashboard](docs/screenshots/dashboard.png) |

| AI Summarizer | Admin Panel |
|---------------|-------------|
| ![Summarizer](docs/screenshots/summarizer.png) | ![Admin](docs/screenshots/admin.png) |

| Members | Billing |
|---------|---------|
| ![Members](docs/screenshots/members.png) | ![Billing](docs/screenshots/billing.png) |

</div>

---

## 🧠 What Is This?

Every B2B SaaS product needs the same unglamorous foundation before the actual product can be built:

- User signup and login
- Organizations and team management
- Role-based access control
- Stripe subscriptions and billing
- Usage limits per plan
- Admin panel to manage everything
- Audit logs for compliance

Building this from scratch takes **4–6 weeks** of careful engineering. LaunchKit collapses that to **hours**.

This is not a tutorial project. Every line is production-quality: secure password hashing, JWT RS256 with refresh token theft detection, atomic usage metering, idempotent Stripe webhooks, row-level tenant isolation. The kind of foundation a paying customer can actually depend on.

---

## ✨ Features

### 🔐 Authentication
- Email/password signup and login with **Argon2id** password hashing
- **JWT RS256** access tokens (15-minute expiry)
- Refresh token rotation with **family-based theft detection** — if a revoked token is replayed, the entire token family is invalidated
- Google OAuth 2.0 with account linking
- Password reset via email link (DB-stored tokens, not JWTs — immediately invalidatable)
- Email verification flow
- Session restoration on page reload

### 🏢 Organizations & Multi-tenancy
- Multi-user workspaces — one user can belong to multiple orgs
- **Row-level tenant isolation** enforced at the SQLAlchemy session layer — physically impossible to leak cross-tenant data
- Org switching without re-authentication (active org via `X-Active-Org` header)
- Invitation flow with 7-day expiry and email delivery

### 🛡️ Role-Based Access Control
- Three roles: **owner** (100) · **admin** (50) · **member** (10)
- Role levels stored in DB — integer comparison, not enum
- FastAPI dependency injection: `require_role(minimum_level)` applied per route
- Owner protection: cannot demote the last owner, cannot grant higher-than-own role

### 💳 Stripe Billing
- **Stripe Checkout** for subscription creation
- **Customer Portal** for self-serve plan management and cancellation
- Full subscription state machine: `free → trialing → active → past_due → canceled → expired`
- **Idempotent webhook handling** — `stripe_events` table with unique constraint prevents duplicate processing
- 7-day grace period on payment failure before downgrade
- Plan metadata (price IDs, limits) stored in DB — no runtime Stripe API lookups

### 📊 Usage Metering
- **Atomic pre-flight check** via conditional PostgreSQL `UPDATE ... WHERE count < limit RETURNING count`
- Zero race conditions — no optimistic locking needed
- Compensating decrement if AI call fails after increment
- Monthly reset via APScheduler job (SQLite job store)
- Per-org usage dashboard with visual progress bar

### 🤖 Demo AI Feature — Meeting Summarizer
- Paste a meeting transcript → get structured JSON output
- Extracts: **summary**, **action items** (with owners and due dates), **key decisions**, **participants**
- Direct OpenAI REST via `httpx` — no SDK dependency
- Retry with corrective prompt on invalid JSON response
- **Per-call cost tracking** in USD, attributed to tenant
- Usage metering enforced before every AI call (402 if limit reached)
- All results stored and scoped to tenant

### 🔧 Admin Panel
- Superadmin-only endpoints protected by `is_superadmin` flag
- User management: disable/enable accounts
- Org overview with subscription and member counts
- **Subscription override** — manually set any org's plan and status
- **Usage override** — manually adjust counters (e.g. reset for a specific org)
- **Audit log viewer** with filtering by org, user, and event type

### 📋 Audit Logging
- Append-only, immutable event trail
- Every sensitive action logged: signup, login, role changes, billing events, AI calls, admin actions
- `actor_id ≠ user_id` distinction — tracks who did it vs whose data was changed
- Never raises — AuditService catches all exceptions internally

### ⚙️ Infrastructure
- **APScheduler** with SQLite job store — monthly usage reset, 7-day subscription expiry check
- **SMTP email service** abstracted behind an interface — swappable to Resend/SendGrid without changing callers
- Rate limiting per user (in-memory, v1)
- Full **Alembic** migration history
- **Docker Compose** for local Postgres

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│              React + Vite Frontend                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  Auth    │  │  App     │  │  Admin Panel     │   │
│  │  Pages   │  │  Pages   │  │                  │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
└─────────────────────┬───────────────────────────────┘
                      │ JWT-authenticated REST
                      │ X-Active-Org header
                      ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend                        │
│  ┌────────────────────────────────────────────┐     │
│  │  Middleware: Auth → Tenant Scope → RBAC    │     │
│  └─────────────────┬──────────────────────────┘     │
│                    │                                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐   │
│  │  Auth   │ │  Org    │ │ Billing │ │    AI    │   │
│  │ Service │ │ Service │ │ Service │ │ Service  │   │
│  └─────────┘ └─────────┘ └────┬────┘ └──────────┘   │
│                               │                     │
│  ┌────────────────────────────┴────────────────┐    │
│  │  Audit Log · Usage Meter · APScheduler      │    │
│  └─────────────────────────────────────────────┘    │
└────────────────┬────────────────────┬───────────────┘
                 │                    │
                 ▼                    ▼
        ┌────────────────┐    ┌──────────────┐
        │  PostgreSQL    │    │    Stripe    │
        │  (tenant-      │    │   (billing)  │
        │   scoped rows) │    │              │
        └────────────────┘    └──────────────┘
```

### Request Lifecycle

```
Request arrives
    │
    ▼
AuthMiddleware          → validates JWT, attaches user
    │
    ▼
TenantScopeMiddleware   → reads X-Active-Org, validates membership,
    │                     installs SQLAlchemy session filter
    ▼
RBACMiddleware          → checks role.level >= required_level
    │
    ▼
Route handler           → all DB queries auto-scoped to tenant_id
    │
    ▼
AuditService            → append-only event log (never raises)
```

---

## 🗄️ Database Schema

**15 tables across two categories:**

**Global (no tenant filter):**
`plans` · `users` · `organizations` · `roles` · `org_memberships` · `invitations` · `refresh_tokens` · `password_reset_tokens` · `email_verification_tokens` · `stripe_events`

**Tenant-scoped (auto-filtered by org_id):**
`usage_counters` · `usage_events` · `audit_logs` · `ai_summaries`

Every table: `UUID primary key`, `created_at`, `updated_at`.

---

## 🧱 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 + Vite, React Router, pure CSS variables |
| **Backend** | FastAPI (Python 3.11), Pydantic v2, SQLAlchemy 2.0 async |
| **Database** | PostgreSQL 16 (Docker), Alembic migrations |
| **Auth** | PyJWT RS256, Argon2id, Google OAuth 2.0 |
| **Billing** | Stripe SDK — Checkout, Customer Portal, Webhooks |
| **AI** | OpenAI GPT-4o-mini via direct REST (httpx — no SDK) |
| **Jobs** | APScheduler with SQLite job store |
| **Email** | SMTP (abstracted — swappable to Resend/SendGrid) |
| **Infrastructure** | Docker Compose, Alembic |

---

## 📁 Project Structure

```
launchkit/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app + lifespan
│   │   ├── config.py               # Pydantic settings
│   │   ├── database.py             # Async engine, get_db, get_admin_db
│   │   ├── models/                 # SQLAlchemy models (one file per domain)
│   │   ├── schemas/                # Pydantic v2 request/response schemas
│   │   ├── routers/                # Thin route handlers
│   │   ├── services/               # All business logic
│   │   │   ├── auth_service.py     # Signup, login, refresh, logout
│   │   │   ├── org_service.py      # Org CRUD, member management
│   │   │   ├── billing_service.py  # Stripe + subscription state machine
│   │   │   ├── usage_service.py    # Atomic metering + cost tracking
│   │   │   ├── ai_service.py       # Meeting summarizer pipeline
│   │   │   ├── audit_service.py    # Append-only event logging
│   │   │   ├── invitation_service.py
│   │   │   └── user_service.py     # Password reset, email verification
│   │   ├── middleware/
│   │   │   ├── auth.py             # JWT validation, get_current_user
│   │   │   ├── tenant.py           # Tenant scope + get_tenant_db
│   │   │   └── rbac.py             # require_role dependency
│   │   ├── core/
│   │   │   ├── security.py         # Argon2, JWT, refresh token utils
│   │   │   ├── openai_client.py    # Direct REST client (no SDK)
│   │   │   ├── email.py            # SMTP email service
│   │   │   ├── stripe_client.py    # Stripe wrapper
│   │   │   └── exceptions.py       # Typed HTTP exceptions
│   │   └── jobs/
│   │       ├── scheduler.py        # APScheduler setup
│   │       ├── usage_reset.py      # Monthly counter reset
│   │       └── subscription_expiry.py  # 7-day grace period enforcement
│   ├── alembic/                    # Migration history
│   ├── seed/                       # Roles, plans, superadmin
│   ├── generate_keys.py            # RSA key pair generation
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/                    # Per-domain API clients
│       ├── context/                # AuthContext, OrgContext
│       ├── components/             # Layout, common UI, billing
│       ├── pages/                  # auth/, dashboard/, ai/, settings/, admin/
│       └── styles/                 # CSS variables + global styles
├── docs/
│   └── screenshots/
└── docker-compose.yml
```

---

## 🚀 Local Setup

### Prerequisites
- Python 3.11
- Node.js 18+
- Docker Desktop

### 1. Clone and configure

```bash
git clone https://github.com/BadrDyane/launchkit.git
cd launchkit
```

### 2. Start Postgres

```bash
docker-compose up -d
```

### 3. Backend setup

```bash
cd backend

# Windows
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS/Linux
python3.11 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

# Generate RSA keys
python generate_keys.py

# Copy and configure environment
cp .env.example .env
# Edit .env — set OPENAI_API_KEY and SMTP credentials
```

### 4. Run migrations and seed

```bash
alembic upgrade head
python -m seed.seed
python -m seed.create_superadmin
```

### 5. Start backend

```bash
uvicorn app.main:app --reload --reload-dir app --port 8000
```

### 6. Frontend setup

```bash
cd ../frontend
npm install
cp .env.example .env   # or create .env with VITE_API_URL=http://127.0.0.1:8000
npm run dev
```

Open `http://localhost:5173`

### Demo accounts

| Email | Password | Role |
|-------|----------|------|
| `alex@acme.com` | `Demo1234!` | Org owner |
| `admin@meetingmind.app` | `Demo1234!` | Superadmin |

---

## 🔑 Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://launchkit:launchkit@127.0.0.1:5433/launchkit

# JWT (RS256 — generated by generate_keys.py)
JWT_PRIVATE_KEY_PATH=./keys/private.pem
JWT_PUBLIC_KEY_PATH=./keys/public.pem
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_PRICE_ID=price_...
STRIPE_BUSINESS_PRICE_ID=price_...

# OpenAI (direct REST — no SDK)
OPENAI_API_KEY=sk-...
OPENAI_DEFAULT_MODEL=gpt-4o-mini

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

---

## 🔌 API Reference

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/signup` | Create account + default org |
| `POST` | `/auth/login` | Login, returns JWT + refresh token |
| `POST` | `/auth/refresh` | Rotate refresh token |
| `POST` | `/auth/logout` | Revoke refresh token |
| `GET` | `/auth/me` | Current user profile |
| `GET` | `/auth/google` | Initiate Google OAuth |

### Organizations
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/org/my-orgs` | List user's organizations |
| `GET` | `/org/` | Active org details |
| `GET` | `/org/members` | List members |
| `POST` | `/org/invitations` | Invite member |
| `POST` | `/org/invitations/accept` | Accept invitation |

### Billing
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/billing/status` | Current plan + subscription status |
| `POST` | `/billing/checkout` | Create Stripe Checkout session |
| `POST` | `/billing/portal` | Create Stripe Customer Portal session |
| `POST` | `/billing/webhook` | Stripe webhook handler |

### AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ai/summarize` | Summarize meeting transcript |
| `GET` | `/ai/summaries` | List past summaries |
| `GET` | `/ai/summaries/{id}` | Get single summary |
| `GET` | `/usage/` | Current usage stats |

### Admin (superadmin only)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin/stats` | Platform-wide statistics |
| `GET` | `/admin/users` | List all users |
| `GET` | `/admin/orgs` | List all organizations |
| `POST` | `/admin/orgs/{id}/subscription-override` | Override plan/status |
| `GET` | `/admin/audit-logs` | View audit trail |

---

## 🔒 Security Decisions

**Password hashing:** Argon2id (memory-hard, GPU-resistant) via `argon2-cffi`. Parameters: time_cost=2, memory_cost=64MB, parallelism=2.

**JWT:** RS256 (asymmetric) — private key signs, public key verifies. Access tokens expire in 15 minutes. Refresh tokens are 32 random bytes stored as SHA-256 hashes — the raw token is never stored.

**Refresh token theft detection:** All tokens in a rotation chain share a `family_id`. If a revoked token is replayed, the entire family is invalidated — forces re-authentication.

**Tenant isolation:** SQLAlchemy `do_orm_execute` event listener appends `WHERE org_id = :tenant_id` to every query on tenant-scoped models. Not enforced at the application layer — enforced at the ORM layer. Admin endpoints use a separate `get_admin_db()` session that bypasses the filter.

**Stripe webhooks:** Signature verification via `stripe.Webhook.construct_event`. Idempotency enforced by inserting `stripe_event_id` into a unique-constrained table — duplicate events return 200 without processing.

**Usage metering:** Atomic conditional `UPDATE ... WHERE count < limit RETURNING count`. If 0 rows updated → limit reached → 402. No optimistic locking, no race conditions.

**CORS:** Explicit `ALLOWED_ORIGINS` from environment variable. Never wildcard with credentials.

---

## 💼 Freelance Use Case

LaunchKit is the foundation I deploy under every client SaaS MVP. It enables:

| Offering | Enabled by |
|----------|-----------|
| **AI SaaS MVP in 3 weeks** — from $5,000 | Auth + billing + multi-tenancy already solved |
| **Vertical AI SaaS** (legal, medical, real estate) — $8K–$15K | Add the domain layer on top of LaunchKit |
| **White-label agency platform** — $10K–$25K | Multi-tenant architecture already in place |

Without LaunchKit, the same MVP takes 8–10 weeks. The template multiplies effective hourly rate by 2–3x.

---

## 🧠 What This Project Demonstrates

- **Production SaaS engineering** — auth, billing, multi-tenancy done correctly, not as demos
- **Security fundamentals** — JWT RS256, Argon2id, token theft detection, webhook verification, atomic metering
- **Multi-tenant architecture** — row-level isolation enforced at ORM layer, not application layer
- **Stripe integration depth** — full subscription lifecycle, not just "accept payments"
- **AI product engineering** — cost tracking, usage metering, structured output validation, retry logic
- **Operational maturity** — audit logs, background jobs, idempotency, graceful degradation
- **Clean architecture** — thin routers, service layer, typed schemas, dependency injection throughout

---

## 👤 Author

**Badr Dyane** — Full-Stack AI & Automation Engineer

Building AI-powered SaaS products and automation systems for startups and SMBs.

- 🌐 [Portfolio](https://portfolio-sigma-beryl-11.vercel.app)
- 💼 [Upwork](https://www.upwork.com/freelancers/)
- 🐙 [GitHub](https://github.com/BadrDyane)
- 📧 badrdyane@gmail.com

---

## 📄 License

MIT — use it, fork it, build on it.

---

<div align="center">

**Built phase by phase. Verified at every step. Production-ready from day one.**

</div>