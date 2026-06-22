# SysDiag Pro

**SysDiag Pro** is a Flask-based System Diagnostic Web App that collects and visualizes host system metrics (CPU, RAM, Disk, Network, Processes), provides security checks, interactive dashboards, automated email reports, and simple admin management. It uses Python, Flask, psutil, Chart.js, and SQLite for a lightweight, self-hostable monitoring solution.

---

## One-line summary
Lightweight Flask web app for local system diagnostics with interactive dashboards, scheduled reports, and admin management.

---

## Features
- Secure user registration and login
- Per-user system scans that collect CPU, RAM, disk, network, process and device information
- Interactive charts (donut and bar) for current and historical metrics (Chart.js)
- Security score calculation and detailed security check breakdown
- Run-on-demand scans and an animated scan UI
- Internet speed testing (speedtest-cli) with history
- Email report delivery (SMTP) with HTML-formatted summary
- Admin panel for viewing users, platform reports, and basic management
- SQLite database for persistence (data/sysdiag.db)

---

## Tech stack
- Backend: Python, Flask
- System collection: psutil, GPUtil, screeninfo
- Speed test: speedtest-cli
- Email: smtplib via settings in `.env`
- Database: SQLite (file-based)
- Frontend: HTML, CSS, JavaScript, Chart.js, Font Awesome

---

## Prerequisites
- Python 3.8+ (3.10/3.11 recommended)
- pip
- On Linux: build tools for optional native deps (e.g., `dmidecode`, `dmidecode` may require sudo)
- An SMTP account or credentials (Gmail app password recommended) configured in `.env`

---

## Quick start (development)
1. Clone the repository:

   git clone https://github.com/harisaravanan1030/System-Diagnostic-Web-App.git
   cd System-Diagnostic-Web-App

2. Create and activate a virtual environment:

   python -m venv venv
   source venv/bin/activate    # macOS / Linux
   venv\Scripts\activate     # Windows (PowerShell/CMD)

3. Install dependencies:

   pip install -r requirements.txt

4. Configure environment variables:

   - Copy `.env` to `.env.local` (or edit `.env`) and set SENDER_EMAIL and SENDER_PASSWORD.
   - Important: Do NOT commit real credentials to the repo.

   Example `.env` keys used:
   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SENDER_EMAIL=your_email@gmail.com
   SENDER_PASSWORD=your_app_password
   ```

5. Run the app locally:

   python app.py

   - The app runs by default at http://127.0.0.1:5000
   - The database is created automatically under `data/sysdiag.db` by `database.init_db()` on import.

6. Default admin credentials (created automatically on first run):

   - Email: admin@sysdiag.com
   - Password: Admin@123

   Change the default admin password immediately in production.

---

## Usage
- Register a user or login with the default admin account.
- From the dashboard, click "Run New Diagnostic" to perform a system scan.
- After scan completes you'll see CPU, RAM, Disk donuts, history charts, security score and quick-fix suggestions.
- Use the Speed Test screen to run internet tests and view history.
- Admin panel (/admin) lists users and all reports and exposes delete actions.

---

## Important files and structure
```
root
├── app.py               # Flask application (routes & controllers)
├── database.py          # SQLite database helpers and schema initialization
├── scanner.py           # System metrics collection (psutil, platform calls)
├── speed_test.py        # speedtest wrapper
├── email_sender.py      # SMTP HTML report sender
├── requirements.txt     # Python dependencies
├── data/                # DB file created here (data/sysdiag.db)
├── templates/           # Jinja2 templates (dashboard, admin, auth pages)
└── static/              # CSS/JS assets (style.css, script.js)
```

---

## API / Endpoints (important ones)
- POST /scan — Run a system scan (requires authentication)
- POST /speedtest — Run speed test (requires authentication)
- GET /dashboard — User dashboard (HTML)
- GET /admin — Admin dashboard (HTML)
- GET /admin/users — JSON list of users (admin-only)
- GET /admin/reports — JSON list of reports (admin-only)
- DELETE /report/<id> — Delete a report (user or admin)
- DELETE /admin/user/<id> — Admin delete user

---

## Development & Recommendations (essentials for the repository)
Below are the immediate repository improvements and essential tasks to make the project safe, maintainable, and contributor-friendly.

1. Remove credentials from version control
   - Do NOT commit `.env` with real credentials. Replace `.env` with `.env.example` containing placeholder values and add `.env` to `.gitignore`.

2. Add `.gitignore`
   - Ignore `venv/`, `data/`, `.env`, `__pycache__/`, `*.pyc`.

3. Add `README.md` (this file) and keep it updated with setup/run instructions.

4. Add a license file
   - Add `LICENSE` (MIT or your preferred license) so users know reuse terms.

5. Add CONTRIBUTING.md and CODE_OF_CONDUCT.md
   - Provide contribution guidelines and standards for PRs/issues.

6. Add SECURITY.md
   - Explain how to disclose vulnerabilities and which versions are supported.

7. Move secret/default values to environment and use config
   - Replace app.secret_key = os.urandom(24) with a secret loaded from environment for reproducible sessions (e.g., SECRET_KEY env var).

8. Add Docker support
   - Create `Dockerfile` and `docker-compose.yml` for easier local testing and deployment.

9. Add tests and CI
   - Create unit tests for `scanner.py`, `database.py` helper functions and run them via GitHub Actions.

10. Use dependency management
   - Keep `requirements.txt` updated and consider pinning exact versions and enabling Dependabot or pip-tools.

11. Protect DB integrity
   - Enable `PRAGMA foreign_keys = ON;` consistently before operations or use SQLAlchemy for higher-level safety.

12. Avoid running shell commands as root or without checks
   - Some scanner functions call `dmidecode`/`wmic` which may require elevated privileges — document this.

13. Improve security checks
   - Sanitize user input and add CSRF protection if switching to Flask forms; consider Flask-Login for session handling.

14. Remove .env from repo and add `.env.example`
   - Provide instructions to copy `.env.example` to `.env`.

15. Add database migration tool (optional)
   - Consider switching to Flask-Migrate / Alembic if schema changes are expected.

16. Add rate limiting and auth for API endpoints
   - Prevent abuse of /scan and /speedtest endpoints by unauthenticated or rate-limited users.

17. Document known limitations and supported OS
   - scanner.py contains many OS-specific heuristics; document supported OS (Windows/Linux) and any limitations.

18. Improve error handling and logging
   - Add structured logging (Python logging module) and graceful error responses.

---

## Quick .gitignore suggestion
```
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
venv/
env/

# Env
.env
.env.*

# Database
/data/
*.db

# Editor
.vscode/
.idea/

# System
.DS_Store

```

---

## Security notes
- Do not commit real email credentials or secrets. Use GitHub Secrets for CI and environment variables when deploying.
- Change the default admin password immediately.
- Running parts of the scanner may require elevated permissions; avoid running as root unless necessary.

---

## Contributing
Contributions are welcome. Please open issues for bugs or feature requests and create pull requests for fixes. Include tests for new features.

---

## License
Add a `LICENSE` (suggest MIT) — include a short header here once you choose one.

---

If you want, I can:
- Add a `.gitignore` file, `.env.example` and replace the committed `.env` with a placeholder (I will not overwrite secrets).
- Create a simple `Dockerfile` and `docker-compose.yml`.
- Add a GitHub Actions workflow for tests and linting.

Tell me which of these you'd like me to add and I'll commit them to your repository.