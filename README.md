# NoteNest

NoteNest is a public academic notes library. Visitors can discover notes by
keyword, subject, academic year, and semester, open a note's detail page, and
download the PDF without logging in. Registered users can upload a PDF with
metadata. It is a lightweight college project built as a small, functional,
testable MVP.

## Features included in the MVP

- Browse, search, and download published notes without logging in.
- Keyword search across title, description, subject, and topic
  (case-insensitive).
- Filters for subject (case-insensitive, matches any part of the subject),
  academic year (1-4), and semester (1-8), combined with AND semantics.
- Sorting by `newest` or `downloads` and paginated results.
- Account registration and login (email + password) with a signed,
  HttpOnly session cookie.
- Email verification: a 6-digit one-time code is emailed at signup; uploading
  is blocked until the code is confirmed (browsing and downloads stay open).
  Codes are hashed at rest, expire after 10 minutes, cap failed attempts, and
  resend is rate-limited.
- Upload a PDF with metadata (title, description, subject, year, semester,
  topic) while logged in.
- Note detail page with metadata, file size, upload date, and download count.
- Safe PDF download.
- A seed command that loads demo notes for local development.
- Responsive, dark-first UI following the ChaiUI design skill.

Explicitly out of scope: upload ownership/roles, comments, ratings, bookmarks,
profiles, admin/moderation tools, password reset, passwordless login, AI
features, and recommendations.

## Architecture overview

```text
Visitor
  |
  v
React + Vite frontend  (fetch / REST)
  |
  v
FastAPI application
  |---------------------------|
  v                           v
SQLAlchemy + SQLite        File service
  |                           |
  v                           v
Note metadata              Local PDF storage
  |                           |
  +----------- API response --+
              |
              v
           React UI
```

Responsibilities:

- **React:** pages, forms, search/filter controls, auth state, loading/error/
  empty states, and navigation.
- **FastAPI:** request validation, endpoints, query handling, upload/download
  orchestration, authentication, and error handling.
- **SQLAlchemy:** ORM mapping and queries.
- **SQLite:** user accounts plus note metadata and counters (never PDF bytes).
- **File service (`backend/app/services/files.py`):** PDF validation, safe
  random filenames, storage, safe path resolution, and cleanup.
- **Security (`backend/app/security.py`):** Argon2id password and OTP hashing,
  one-time-code generation, and JWT session tokens.
- **Email (`backend/app/email.py`):** sends the verification code over SMTP
  using only the standard library; when SMTP is not configured it writes the
  code to the log instead (development and tests run fully offline).
- The frontend only talks to the REST API; it never touches SQLite or server
  files directly.

## Technology stack

- **Frontend:** React 19, Vite, JavaScript, React Router, Tailwind CSS v4, and
  the ChaiUI design tokens/utilities. HTTP via the browser Fetch API.
- **Backend:** Python, FastAPI, Pydantic v2, SQLAlchemy 2.x, SQLite,
  `python-multipart`, `uvicorn`, `argon2-cffi` (password and OTP hashing),
  `PyJWT` (session tokens), `email-validator`, and the standard-library
  `smtplib` for outbound email.
- **Tests:** `pytest` and the FastAPI `TestClient` (`httpx`).
- **Storage:** SQLite for metadata, local filesystem for PDFs (development).

## Prerequisites

- Python 3.11+ (developed on 3.12).
- Node.js 18+ and npm (developed on Node 24).

## Backend setup

From the `backend` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The API serves at http://127.0.0.1:8000.

To load demo notes for a fresh development database:

```powershell
python -m app.seed
```

Seeding is idempotent: it skips samples that already exist by title and never
deletes data. With an empty database it creates ten fictional notes covering
multiple subjects, years 1-4, and semesters 1-8.

## Frontend setup

From the `frontend` directory:

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

The app serves at http://localhost:5173. Open that URL (Vite binds
`localhost`; use `localhost`, not `127.0.0.1`, in the browser).

To produce a production bundle:

```powershell
npm run build
npm run preview
```

## Environment variables

Backend (all optional, with development defaults):

| Variable | Default | Purpose |
| --- | --- | --- |
| `NOTENEST_DATABASE_URL` | `sqlite:///<backend>/notenest.db` | SQLAlchemy database URL |
| `NOTENEST_UPLOAD_DIR` | `<backend>/uploads` | Directory for stored PDFs |
| `NOTENEST_MAX_UPLOAD_SIZE` | `10485760` (10 MB) | Maximum upload size in bytes |
| `NOTENEST_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated allowed browser origins |
| `NOTENEST_SECRET_KEY` | dev placeholder | HMAC key that signs session tokens (set a long random value in production) |
| `NOTENEST_ACCESS_TOKEN_TTL` | `86400` (24h) | Session lifetime in seconds |
| `NOTENEST_COOKIE_NAME` | `notenest_session` | Session cookie name |
| `NOTENEST_COOKIE_SECURE` | `false` | Send the cookie only over HTTPS (set `true` in production) |
| `NOTENEST_COOKIE_SAMESITE` | `lax` | Session cookie SameSite policy |
| `NOTENEST_SEED_ON_STARTUP` | `false` | Load demo notes on startup when the library is empty (for ephemeral hosts) |
| `NOTENEST_SMTP_HOST` | `smtp.gmail.com` | SMTP server for verification email |
| `NOTENEST_SMTP_PORT` | `587` | SMTP port |
| `NOTENEST_SMTP_USE_TLS` | `true` | Use STARTTLS for the SMTP connection |
| `NOTENEST_SMTP_USER` | *(empty)* | SMTP username; empty disables real sending (codes are logged instead) |
| `NOTENEST_SMTP_PASSWORD` | *(empty)* | SMTP password or app password |
| `NOTENEST_SMTP_FROM` | *(empty)* | From address; defaults to `NOTENEST_SMTP_USER` |
| `NOTENEST_OTP_LENGTH` | `6` | Number of digits in the verification code |
| `NOTENEST_OTP_TTL_SECONDS` | `600` (10 min) | How long a code stays valid |
| `NOTENEST_OTP_MAX_ATTEMPTS` | `5` | Wrong guesses allowed before a new code is required |
| `NOTENEST_OTP_RESEND_COOLDOWN_SECONDS` | `60` | Minimum wait between resend requests |

Frontend:

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` (dev); `/api/v1` (prod) | Base URL of the backend API |

The only secret is `NOTENEST_SECRET_KEY`. The development default is an
insecure placeholder; always set a real, long, random value in production and
never commit a real `.env` file. `backend/.env.example` lists every setting.

### Email verification setup (optional)

Email sending is off by default: with `NOTENEST_SMTP_USER` empty the app runs
in development mode and the verification code is printed to the server log
(look for `verification code for <email> is <code>`), so the whole flow works
with no mail account.

To send real email with Gmail:

1. Enable 2-Step Verification on the Google account.
2. Create an **App Password** at https://myaccount.google.com/apppasswords.
3. Set `NOTENEST_SMTP_USER` to the Gmail address and `NOTENEST_SMTP_PASSWORD`
   to the 16-character app password (no spaces). `NOTENEST_SMTP_HOST` and
   `NOTENEST_SMTP_PORT` already default to Gmail's.

Any other SMTP provider (Brevo, a university mail server, and so on) works the
same way by changing the host, port, user, and password.

## How to run tests

Backend suite (from the `backend` directory):

```powershell
python -m pytest
```

Tests run against an isolated temporary SQLite database and upload directory;
they never touch the development database.

## API docs

Interactive documentation is available while the backend runs:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- OpenAPI schema: http://127.0.0.1:8000/openapi.json

Health probe: `GET http://127.0.0.1:8000/health`.

### Endpoints (all under `/api/v1`)

- `GET /api/v1/notes` - list, search, filter, sort, and paginate notes.
- `POST /api/v1/notes` - upload a PDF with metadata (multipart form; requires
  an authenticated session with a verified email).
- `GET /api/v1/notes/{note_id}` - public metadata for one note.
- `GET /api/v1/notes/{note_id}/download` - download the PDF.
- `POST /api/v1/auth/register` - create an account, start a session, and email a
  verification code.
- `POST /api/v1/auth/login` - start a session.
- `POST /api/v1/auth/logout` - end the session.
- `GET /api/v1/auth/me` - the current user for an existing session.
- `POST /api/v1/auth/verify-email` - confirm the email with the emailed code.
- `POST /api/v1/auth/resend-otp` - send a new code (rate-limited by a cooldown).

## Authentication and security

- Passwords are hashed with **Argon2id** (`argon2-cffi`) and never stored or
  returned in plain text.
- **Email verification:** registration issues a 6-digit code. Only its Argon2
  hash is stored; it expires after 10 minutes, allows a limited number of
  wrong guesses, and resend is rate-limited to one per minute. Uploading
  requires a verified email; everything else stays public.
- A successful register/login issues a signed JWT session token
  (`PyJWT`, HS256) in an **HttpOnly** cookie (`notenest_session`), so frontend
  JavaScript can never read it. The cookie is `SameSite=Lax` and scoped to
  `path=/`.
- Email addresses are normalized (trimmed and lowercased) and unique. Login
  failures return a generic `Invalid email or password` message.
- CSRF defense in depth: `SameSite=Lax` for normal flows plus middleware that
  rejects state-changing requests from an `Origin` that is not in
  `NOTENEST_CORS_ORIGINS` with `403 {"detail": "Origin not allowed"}`.
- CORS allows credentials for the configured origins (never a wildcard with
  credentials).
- Browsing, search, filters, detail, and downloads are public; only upload
  requires a session (with a verified email).
- For production, set `NOTENEST_SECRET_KEY` to a long random value, serve over
  HTTPS, and set `NOTENEST_COOKIE_SECURE=true`.

## Local SQLite and upload storage behavior

- The SQLite database file is created automatically on startup at
  `backend/notenest.db` (configurable). Tables (`notes` and `users`) are created
  if missing and are never dropped.
- Uploaded PDFs are written to `backend/uploads` (configurable) under
  server-generated random names, outside the frontend's served directory.
- PDF bytes are never stored in the database; only metadata and a reference
  are.
- The application does not expose physical file paths, and there is no public
  delete endpoint.

## Known limitations

- **Uploads require an account, but there is no ownership or moderation.**
  Any logged-in user can upload, and notes are not tied to a user or editable.
  Before any real public launch, add upload ownership, roles, abuse
  prevention, rate limiting, and content moderation.
- **No password reset.** Email verification exists, but there is no
  forgot-password flow. Accounts are email + password only.
- **No delete/edit.** Notes cannot be edited or removed through the API.
- **SQLite + local files.** Suitable for development and a small demo, but not
  for concurrent production traffic.
- **Frontend has no automated test suite.** The backend has an automated
  `pytest` suite; frontend flows were verified manually against the live API.
- A pre-existing development database created before an index was added may be
  missing that index, because `create_all` does not alter existing tables.
- The Starlette/`httpx` `TestClient` deprecation warning is harmless.

## Deployment requirements

Do not deploy without verifying persistent storage. Requirements:

- **Frontend:** static hosting of the `frontend` build (`npm run build`).
- **Backend:** a Python-compatible host running the FastAPI app (for example
  `uvicorn app.main:app`).
- **Persistent database storage:** a durable volume or a managed database.
- **Persistent PDF storage:** a durable volume or object storage.
- **Correct frontend API URL:** set `VITE_API_BASE_URL` at build time to the
  deployed backend URL (production builds default to the same-origin `/api/v1`).
- **Correct CORS origins:** set `NOTENEST_CORS_ORIGINS` to the deployed
  frontend origin.
- **Auth hardening:** set a long random `NOTENEST_SECRET_KEY`, serve over
  HTTPS, and set `NOTENEST_COOKIE_SECURE=true`.
- **Environment variables:** configure all of the variables listed above.

## Deploying on free tiers (Vercel frontend + Render backend)

The app runs entirely on free tiers: the React app is hosted by Vercel and the
API by Render, and the frontend calls the backend directly.

```text
Browser -> https://<app>.vercel.app              (static React app)
             |  fetch https://<render-service>.onrender.com/api/v1/*
             v
        https://<render-service>.onrender.com    (FastAPI + SQLite + uploads)
```

**1. Backend on Render**

1. Push this repo to GitHub.
2. In Render: **New + -> Web Service**, connect the repo.
3. Settings:

   | Field | Value |
   | --- | --- |
   | Root Directory | `backend` |
   | Runtime | Python 3 |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | Instance Type | Free |
   | Health Check Path | `/health` |

4. Environment variables:

   | Key | Value |
   | --- | --- |
   | `PYTHON_VERSION` | `3.12.2` |
   | `NOTENEST_SECRET_KEY` | a long random string (32+ characters) |
   | `NOTENEST_COOKIE_SECURE` | `true` |
   | `NOTENEST_COOKIE_SAMESITE` | `none` |
   | `NOTENEST_SEED_ON_STARTUP` | `true` |
   | `NOTENEST_CORS_ORIGINS` | `https://<app>.vercel.app` |
   | `NOTENEST_SMTP_USER` | your Gmail address (see the email-verification notes below) |
   | `NOTENEST_SMTP_PASSWORD` | your 16-character Gmail **App Password** |

   (`NOTENEST_SMTP_HOST`/`NOTENEST_SMTP_PORT` already default to Gmail. Leave
   the two SMTP values unset to run in development mode, where codes are only
   printed in the Render logs.)

5. Deploy and note the service URL, for example
   `https://notenest-api.onrender.com`. Check `https://<service>/health`.

The frontend and API are on different sites, so the session cookie must be
cross-site: use `NOTENEST_COOKIE_SAMESITE=none` together with
`NOTENEST_COOKIE_SECURE=true` (browsers require `Secure` for `SameSite=None`).

**2. Frontend on Vercel**

1. In Vercel: **Add New -> Project**, import the repo.
2. Set **Root Directory** to `frontend`. Vercel detects Vite; the build command
   `npm run build` and output `dist` are correct.
3. Add an environment variable **`VITE_API_BASE_URL`** set to
   `https://<render-service>.onrender.com/api/v1` (your Render URL). It is read
   at build time, so set it before deploying and redeploy after changing it.
4. Deploy and copy the Vercel URL.

**3. Connect the two**

Set `NOTENEST_CORS_ORIGINS` on Render to the Vercel URL from step 2.4 and
redeploy the backend so the Origin check and CORS allow it.

**Free-tier caveats**

- Render's free plan has an **ephemeral filesystem**: the SQLite database and
  uploaded PDFs reset on every restart or redeploy. `NOTENEST_SEED_ON_STARTUP`
  reloads the demo notes on each boot, so the site is never empty, but accounts
  and uploads do not survive a restart. For lasting data, attach a persistent
  disk (paid) or move to managed Postgres plus object storage.
- Render free services **sleep after ~15 minutes idle**; the first request then
  takes 30-60 seconds to wake. Open the site once before sharing it.
- **Cross-site cookies:** this direct-URL setup uses `SameSite=None; Secure`.
  Some browsers (notably Safari) restrict cross-site cookies and can drop the
  session. Proxying the API through the frontend origin (a Vercel `rewrites`
  rule) avoids this by keeping the cookie first-party; it is not configured
  here and can be added later if sign-in proves flaky.
- **Verification email:** set `NOTENEST_SMTP_USER`/`NOTENEST_SMTP_PASSWORD`
  (a Gmail App Password) so real codes are delivered. Gmail's free limit is
  plenty for a demo; without credentials the codes appear only in the Render
  logs.

## Running a production build locally

```powershell
# Build the frontend and serve it (still talks to the local API)
npm run build
npm run preview
```

## Project layout

```text
backend/
  app/            FastAPI app, models, schemas, routers, file service,
                  security, email, seed
  tests/          pytest suite (isolated temp DB and upload directory)
  requirements.txt
  .env.example    Backend environment placeholders
frontend/
  src/            React app (pages, components, api client, auth, ChaiUI theme)
  index.html
  vite.config.js
  .env.example    Frontend environment placeholders
README.md         This file
LICENSE           MIT license
```

## License

Released under the MIT License. See [LICENSE](LICENSE).
