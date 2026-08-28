# WraithWatch

A DFIR-focused SIEM dashboard I built for my Masters cybersecurity capstone. It ingests logs from a few common sources, runs them through a rule-based detection engine, and gives an analyst a single place to triage alerts instead of digging through raw log files.

## What it does

- Ingests Apache/Nginx, Linux syslog, and Windows Event Log (EVTX) files
- Runs everything through 10 detection rules — brute force, service installs, injection attempts, that kind of thing — with severity scored 1–5
- Incident management: open a case from an alert, track status, leave analyst notes, and it keeps an audit trail of who did what
- Background job flags log sources that have gone quiet or stale
- Pulls IP reputation from AbuseIPDB (cached, since the free tier rate-limits fast)
- Exports a case as a PDF report — useful for handing off to whoever needs it next
- Full-text search across ingested logs, plus a live-tailing view
- JWT auth, bcrypt hashing, basic rate limiting on login, two roles (admin/analyst)

Input is sanitised with bleach before it touches the DB, since log content is attacker-controlled and I didn't want stored XSS in the analyst notes field.

## Stack

Backend is Flask + SQLAlchemy + PyJWT, ReportLab for the PDF export. Frontend is React/Vite with Chart.js for the graphs. SQLite locally, meant to point at Postgres for anything real. 42 pytest tests covering parsers, rules, and the security helpers.

## Running it

**Backend**

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
python app.py
```

First run creates `wraithwatch.db` and seeds it with demo data. API's on `http://localhost:5000`.

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:5173`. Demo login is `analyst` / `Password123!`.

## Config

Copy `.env.example` to `.env`. `DATABASE_URL` can stay blank for SQLite or point at Postgres (`postgresql://user:pass@localhost:5432/wraithwatch`). `ABUSEIPDB_API_KEY` is optional — without it the reputation lookups just no-op. Change `SECRET_KEY` before deploying anywhere real, obviously.

## Tests

```bash
cd backend
python -m pytest ../tests/ -v
```

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

## Known limitations

- Rules are regex-based, not statistical — easy to evade if you know what's being matched
- No real-time streaming ingestion yet, log upload is batch-only
- Rate limiting is in-memory, so it resets on restart and won't work across multiple app instances
- AbuseIPDB free tier caps out fast; caching helps but it's not a real fix

## Academic context

Built for a Masters capstone addressing alert fatigue, workflow fragmentation, and log source visibility in security operations — grounded in seven peer-reviewed papers on SIEM architecture and log forensics (see report for citations).

## Licence

Academic project, not intended for production use.
