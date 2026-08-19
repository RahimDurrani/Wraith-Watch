# WraithWatch

A lightweight, DFIR-focused Security Information and Event Management (SIEM) dashboard built for a Masters cybersecurity capstone project. WraithWatch ingests logs from multiple sources, detects threats through a rule-based engine, and presents them through a clean web interface designed to reduce analyst alert fatigue.

## Features

- **Multi-format log ingestion** — Apache/Nginx, Linux syslog, and Windows Event Logs (EVTX)
- **Rule-based detection engine** — 10 detection rules covering brute force, service installation, privilege escalation, injection attacks, and more
- **Weighted severity scoring** — alerts prioritised 1–5 so analysts see critical threats first
- **Integrated incident management** — case creation, status workflow, analyst notes, and an immutable audit trail
- **Log source health monitoring** — background scheduler flags active, stale, and silent sources
- **IP reputation enrichment** — AbuseIPDB integration with caching
- **One-click forensic PDF export** — professional incident reports generated on demand
- **Full-text log search** — search across all ingested log entries
- **Live log streaming** — real-time view of incoming logs with search and filtering
- **JWT authentication** — bcrypt password hashing, login rate limiting, role-based access control
- **Input sanitisation** — bleach-based XSS protection on all user-supplied content

## Tech stack

**Backend:** Python, Flask, SQLAlchemy, Flask-Bcrypt, PyJWT, ReportLab, bleach, schedule, requests
**Frontend:** React, Vite, Chart.js, Tabler Icons
**Database:** SQLite (development) → PostgreSQL (production)
**Testing:** pytest (42 tests)

## Project structure

```
wraithwatch/
├── backend/
│   ├── app.py                    Flask entry point
│   ├── requirements.txt
│   ├── .env.example
│   ├── models/
│   │   └── database.py           SQLAlchemy models (8 tables)
│   ├── routes/
│   │   ├── auth.py               Login, signup, JWT
│   │   ├── dashboard.py          Alerts, incidents, stats
│   │   ├── upload.py             Log file upload + parsing
│   │   ├── live_logs.py          Real-time log streaming
│   │   └── reports.py            PDF export + log search
│   └── utils/
│       ├── auth.py               JWT helpers, validation
│       ├── parsers.py            Apache/syslog/EVTX parsers
│       ├── rule_engine.py        10 detection rules
│       ├── ip_reputation.py      AbuseIPDB integration
│       ├── health_monitor.py     Background health scheduler
│       ├── log_generator.py      Live log simulation
│       ├── pdf_report.py         Forensic PDF generation
│       ├── security.py           Sanitisation, RBAC, rate limiting
│       └── seeder.py             Demo data seeding
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── components/           Sidebar, shared UI
│       ├── hooks/                useFetch
│       ├── pages/                8 pages
│       └── utils/                constants
└── tests/
    ├── test_parsers.py           21 tests
    ├── test_rules.py             9 tests
    └── test_security.py          12 tests
```

## Getting started

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
python app.py
```

The API runs at `http://localhost:5000`. On first run it creates `wraithwatch.db` with all tables and seed data.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173`.

### Demo login

```
Username: analyst
Password: Password123!
```

## Configuration

Copy `.env.example` to `.env` and configure:

- `DATABASE_URL` — leave blank for SQLite, or set a PostgreSQL URL for production
- `ABUSEIPDB_API_KEY` — optional; enables live IP reputation scores
- `SECRET_KEY` — change to a long random string in production

### Switching to PostgreSQL

1. Install PostgreSQL and create a database
2. Set `DATABASE_URL=postgresql://user:password@localhost:5432/wraithwatch` in `.env`
3. Restart the backend — SQLAlchemy handles the rest

## Testing

```bash
cd backend
python -m pytest ../tests/ -v
```

All 42 tests should pass.

## Detection rules

| Rule | Log type | Severity | Trigger |
|------|----------|----------|---------|
| SSH brute force | syslog | critical | 5 failed logins in 60s |
| Windows service install | evtx | critical | Event 7045 |
| Break-in attempt | syslog | critical | Reverse DNS mismatch |
| Suspicious process | evtx | critical | Event 4688 from Temp/Public |
| Account lockout | evtx | high | Event 4740 |
| Explicit credential logon | evtx | high | Event 4648 |
| Sudo failure | syslog | high | Failed privilege escalation |
| SQL injection | apache | high | Injection patterns in request |
| Path traversal | apache | medium | Directory traversal sequence |
| HTTP scanner | apache | low | 10 probes in 120s |

## Academic context

This project was developed as a Masters cybersecurity capstone, addressing three documented problems in security operations: alert fatigue, workflow fragmentation, and log source visibility. The design and evaluation are grounded in seven peer-reviewed research papers on SIEM architecture, alert fatigue, and log forensics.

## Licence

Academic project — not licensed for production use.
