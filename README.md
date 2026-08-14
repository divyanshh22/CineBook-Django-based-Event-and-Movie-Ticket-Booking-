# CineBook 🎬

A production-style **movie and event ticket booking platform** inspired by BookMyShow — but with an original design, original branding and no copied assets. Discover movies and events, pick a cinema and showtime, choose your seats, pay and carry digital tickets with QR codes.

> **Status:** Phases 1–10 complete — project setup, database, authentication (session + CSRF), the public movies browsing experience (list, filters, search, detail with showtimes and reviews), cinema browsing (list, search, city filter, detail with screens and per-date showtimes), the full booking flow (interactive seat picker with live availability, price preview, 10-minute seat locking, mock payment gateway, QR ticket download), the admin dashboard (stats, revenue chart, movie/cinema/screen/showtime management, seat-layout generation, bookings + users overview) **and the hardening pass** (77 tests, security + performance optimisation). See the [Roadmap](#roadmap) below.

---

## Tech stack

| Layer      | Technology |
|------------|------------|
| Frontend   | React 19 + JavaScript (Vite 8) |
| Backend    | Python + Django 5.2 + Django REST Framework |
| Database   | SQLite (dev default) / PostgreSQL (via `DB_ENGINE=postgres`) |
| Auth       | Django session authentication protected by **CSRF tokens** |
| API        | REST, paginated, filterable |
| Styling    | Modern custom CSS design system (dark theme) |
| Images     | Django media storage (Cloudinary-ready, Phase 2+) |
| Docs       | Auto-generated OpenAPI schema at `/api/schema/` |

## Folder structure

```
CineBook/
├── backend/                    # Django project
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example            # copy to .env
│   ├── config/                 # project settings / urls / wsgi / asgi
│   ├── apps/
│   │   ├── core/               # shared: pagination, exceptions, base model
│   │   └── accounts/           # custom User + auth endpoints
│   ├── templates/
│   ├── media/                  # user uploads (gitignored)
│   └── db.sqlite3              # local dev database (gitignored)
└── frontend/                   # React app (Vite)
    ├── package.json
    ├── vite.config.js          # dev proxy /api + /media -> :8000
    ├── .env.example
    └── src/
        ├── api/client.js       # axios + CSRF interceptor + error handling
        ├── context/AuthContext.jsx
        ├── components/
        │   ├── layout/         # Navbar, Layout
        │   ├── ui/             # Toast, Feedback (spinner/empty/error)
        │   └── ProtectedRoute.jsx
        └── pages/              # Home, Login, Register, ForgotPassword,
                                # ResetPassword, Profile
```

---

## Setup (Phase 1)

### Prerequisites

- Python 3.11+ (tested on 3.13)
- Node.js 20+ and npm
- PostgreSQL 15+ *(optional — only needed if you switch `DB_ENGINE=postgres`)*

### 1. Backend

```bash
cd backend

# Create & activate a virtual environment (from repo root, if not present)
python -m venv .venv            # or use your existing one
.\.venv\Scripts\activate        # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Configure environment
Copy-Item .env.example .env     # then edit .env if needed

# Apply database migrations
python manage.py migrate

# Create an admin superuser
python manage.py createsuperuser

# Run the dev server
python manage.py runserver
```

Backend runs at **http://localhost:8000**.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:5173** and proxies `/api` and `/media` to the backend, so there are no CORS issues in development. CORS is also configured as a fallback for direct cross-origin calls.

### 3. Verify the auth flow

- Open http://localhost:5173 → click **Sign up**, create an account.
- You are logged in automatically; open **My profile** to edit details or change the password.
- Try **Forgot password** — in development the reset link is printed in the backend terminal **and** shown on screen.
- Admin panel: http://localhost:8000/admin (superuser credentials).

---

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DJANGO_SECRET_KEY` | dev-only | Secret key (use a long random value) |
| `DJANGO_DEBUG` | `True` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hosts |
| `DB_ENGINE` | `sqlite` | `sqlite` or `postgres` |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | — | PostgreSQL connection (used when `DB_ENGINE=postgres`) |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Allowed frontend origins |
| `CSRF_TRUSTED_ORIGINS` | same | Trusted origins for CSRF |
| `CSRF_COOKIE_SAMESITE` / `SESSION_COOKIE_SAMESITE` | `Lax` | Cookie scoping |
| `CSRF_COOKIE_SECURE` / `SESSION_COOKIE_SECURE` | `False` | Set `True` behind HTTPS |
| `THROTTLE_*` | varies | API rate limits |
| `EMAIL_BACKEND` | console (dev) / smtp (prod) | Email delivery |
| `DEFAULT_FROM_EMAIL` | CineBook | From address |
| `FRONTEND_RESET_URL` | `http://localhost:5173/reset-password` | Password-reset link target |
| `TIME_ZONE` | `UTC` | Django timezone |

Never commit a real `.env` — use `.env.example` as the template.

---

## Phase 1 — what was implemented

### Backend

- **Restructured** into `backend/` (Django project `config/`) with modular apps under `backend/apps/`.
- **Environment-based settings** via `python-dotenv` (`.env`), including an auto-hardening block when `DEBUG=False` (HSTS, secure cookies, SSL redirect).
- **Custom User model** (`accounts.User`): extends Django's `AbstractUser` with unique email, phone number, avatar, date of birth, email-verified flag, plus a custom manager.
- **Session + CSRF authentication** (no JWT, as requested): DRF `SessionAuthentication` with Django CSRF protection enforced on every state-changing request.
- **Rate limiting** on auth endpoints (`auth` scope: 20/min, `password_reset`: 5/hour).
- **Consistent error handling** through a custom exception handler (`core.exceptions`).
- **Pagination defaults** (`core.pagination`) ready for content APIs in later phases.
- **Password reset flow** using Django's token generator; development mode returns the reset token so it is testable without SMTP.

### Files created / modified

| Path | Notes |
|------|-------|
| `backend/manage.py` | Settings module → `config.settings` |
| `backend/config/settings.py` | Full env-based configuration |
| `backend/config/urls.py` | `/api/auth/*`, `/api/schema/`, `/admin/`, media serving |
| `backend/requirements.txt` | Python dependencies |
| `backend/.env.example` | Environment template |
| `backend/apps/core/*` | `pagination.py`, `exceptions.py`, `TimeStampedModel` |
| `backend/apps/accounts/models.py` | Custom `User` + `UserManager` |
| `backend/apps/accounts/serializers.py` | Register/Login/Profile/Password serializers |
| `backend/apps/accounts/views.py` | Auth API views |
| `backend/apps/accounts/urls.py` | Auth routes |
| `backend/apps/accounts/tokens.py` | Reset token helpers |
| `backend/apps/accounts/admin.py` | User admin with profile fields |
| `backend/apps/accounts/tests.py` | 19 tests |
| `backend/apps/accounts/migrations/0001_initial.py` | User model migration |
| `frontend/*` | Full Vite + React app (see structure above) |

### API endpoints (Phase 1)

All under `/api/auth/`:

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `auth/csrf/` | public | Set/refresh the `csrftoken` cookie |
| GET | `auth/session/` | public | Current session status + user |
| POST | `auth/register/` | public | Create account (auto-login) |
| POST | `auth/login/` | public | Log in (username or email) |
| POST | `auth/logout/` | session | Destroy session |
| GET | `auth/me/` | session | Own profile |
| PATCH | `auth/me/` | session | Update own profile |
| POST | `auth/password/change/` | session | Change own password |
| POST | `auth/password/reset/` | public | Send reset email |
| POST | `auth/password/reset/confirm/` | public | Set new password with token |

**How CSRF works in the browser:** the axios client reads the `csrftoken` cookie on every state-changing request and sends it as `X-CSRFToken`. Django rotates the token on login, which the client picks up automatically.

### Database changes

- SQLite dev database created via `python manage.py migrate` (one table: `accounts_user`, plus Django admin/auth/session tables).
- To switch to **PostgreSQL**: set `DB_ENGINE=postgres` and the `DB_*` variables, then `python manage.py migrate`.

### Tests

```bash
cd backend
python manage.py test apps.accounts
```

19 tests covering registration, login (username & email), logout, session, profile read/update, password change, password reset flow, and CSRF enforcement (requests without a valid token are rejected with 403).

### Frontend highlights

- Vite dev proxy so `fetch`/axios stay same-origin (no CORS friction).
- `api/client.js`: axios instance with `withCredentials`, automatic CSRF header, and normalised `{ message, fieldErrors }` errors.
- `AuthContext`: session bootstrap, login/register/logout/profile/password actions.
- `ProtectedRoute` / `PublicOnlyRoute` guards.
- Toast notifications, loading/empty/error states, mobile-responsive navbar with user dropdown.
- Original dark design system (`index.css`) with violet/cyan gradient accents — no BookMyShow branding.

---

## Testing the API manually

```bash
# 1. Get a CSRF cookie
curl -c cookies.txt http://localhost:8000/api/auth/csrf/

# 2. Register (token comes from the cookie jar)
curl -b cookies.txt -c cookies.txt -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" -H "X-CSRFToken: <token-from-cookie>" \
  -d '{"username":"demo","email":"demo@example.com","password":"Str0ng!Pass123","password_confirm":"Str0ng!Pass123"}'

# 3. View session / profile
curl -b cookies.txt http://localhost:8000/api/auth/session/
curl -b cookies.txt http://localhost:8000/api/auth/me/
```

OpenAPI schema (auto-generated): `http://localhost:8000/api/schema/` — it will be documented/enriched in later phases.

---

## Roadmap

- **Phase 1 (done):** Project setup + database + authentication
- **Phase 2 (done):** Movies + genres + movie details (backend + frontend)
- **Phase 3 (done):** Cinemas + screens + seats (backend + frontend)
- **Phase 4 (done):** Showtimes + seat availability (backend + frontend)
- **Phase 5 (done):** Seat selection + booking system (backend + frontend)
- **Phase 6 (done):** Payment flow (mock, gateway-ready) (backend + frontend)
- **Phase 7 (done):** Tickets + QR codes (backend + frontend — ticket download live on booking detail)
- **Phase 8 (done):** Admin dashboard (stats, revenue chart, movie/cinema/screen/showtime CRUD, seat-layout generation, bookings + users overview)
- **Phase 9 (done):** Reviews + search + filtering (backend + frontend reviews/search live)
- **Phase 10 (done):** Testing + security + performance optimisation — 77 backend tests (booking flow, lock expiry, ownership isolation, admin CRUD, events, filters), hardened env-based settings, graceful 4xx on unknown payment method, `select_related`/`prefetch_related` query optimisation (no N+1), deterministic pagination ordering. Lint + production build clean (2 pre-existing React fast-refresh warnings only).
