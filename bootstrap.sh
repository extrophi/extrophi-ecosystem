#!/usr/bin/env bash
set -euo pipefail

# Re-run with sudo if not root
if [[ "${EUID}" -ne 0 ]]; then
  exec sudo -E bash "$0" "$@"
fi

# Determine the non-root user to run the app as
REAL_USER="${SUDO_USER:-$USER}"
APP_DIR="/opt/project-dashboard"
ROOT_DIR="/home/${REAL_USER}/01-projects"

echo "==> Installing system dependencies"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends \
  curl ca-certificates nginx git python3-venv openssl

echo "==> Installing uv (Python tooling) if missing"
export PATH="${HOME}/.local/bin:${PATH}"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
fi

echo "==> Preparing directories"
mkdir -p "${APP_DIR}/app/templates" "${APP_DIR}/app/static"
mkdir -p "${ROOT_DIR}"
chown -R "${REAL_USER}:${REAL_USER}" "${APP_DIR}" "${ROOT_DIR}"

echo "==> Writing app code"
cat > "${APP_DIR}/requirements.txt" <<'REQ'
fastapi~=0.112
uvicorn[standard]~=0.30
jinja2~=3.1
python-multipart~=0.0.9
REQ

cat > "${APP_DIR}/app/main.py" <<'PY'
from fastapi import FastAPI, Request, HTTPException, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

import os, subprocess
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))
ROOT = Path(os.environ.get("DASHBOARD_ROOT", str(Path.home() / "01-projects"))).expanduser().resolve()
ADMIN_USER = os.environ.get("DASHBOARD_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("DASHBOARD_ADMIN_PASSWORD", "admin")
SECRET = os.environ.get("DASHBOARD_SECRET", "change-me")

app = FastAPI(title="Project Dashboard", docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key=SECRET, same_site="lax", https_only=False)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

def is_authed(request: Request):
    return request.session.get("user") == ADMIN_USER

def login_required(request: Request):
    if not is_authed(request):
        raise HTTPException(status_code=401, detail="Not authenticated")

def safe_join(rel: str) -> Path:
    if rel.startswith("/"):
        rel = rel.lstrip("/")
    p = (ROOT / rel).resolve()
    try:
        p.relative_to(ROOT)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")
    return p

def list_projects():
    if not ROOT.exists():
        return []
    items = []
    for d in sorted([x for x in ROOT.iterdir() if x.is_dir() and not x.name.startswith(".")], key=lambda p: p.name.lower()):
        runfile = d / "run.sh"
        logs_dir = d / "logs"
        last = datetime.fromtimestamp(d.stat().st_mtime, tz=timezone.utc)
        logs = []
        if logs_dir.exists():
            for lf in sorted(logs_dir.glob("*.log")):
                try:
                    lm = datetime.fromtimestamp(lf.stat().st_mtime, tz=timezone.utc)
                except Exception:
                    lm = None
                logs.append({"name": lf.name, "mtime": lm})
        items.append({
            "name": d.name,
            "path": str(d),
            "has_run": runfile.exists(),
            "last_modified": last,
            "logs": logs,
        })
    return items

@app.get("/healthz")
def healthz():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat(), "root": str(ROOT)}

@app.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
    if is_authed(request):
        return RedirectResponse(url="/", status_code=302)
    return TEMPLATES.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
async def post_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["user"] = ADMIN_USER
        return RedirectResponse(url="/", status_code=302)
    return TEMPLATES.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"}, status_code=400)

@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if not is_authed(request):
        return RedirectResponse(url="/login", status_code=302)
    return TEMPLATES.TemplateResponse("dashboard.html", {"request": request, "projects": list_projects(), "root": str(ROOT)})

@app.get("/admin/files", response_class=HTMLResponse)
def files_index(request: Request, p: str = ""):
    if not is_authed(request):
        return RedirectResponse(url="/login", status_code=302)
    target = safe_join(p)
    if not target.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    entries = []
    for x in sorted(target.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
        try:
            mtime = datetime.fromtimestamp(x.stat().st_mtime, tz=timezone.utc)
        except Exception:
            mtime = None
        entries.append({
            "name": x.name,
            "is_dir": x.is_dir(),
            "rel": str((Path(p) / x.name) if p else Path(x.name)),
            "mtime": mtime,
            "size": x.stat().st_size if x.is_file() else None
        })
    breadcrumbs, accum = [], []
    for part in Path(p).parts:
        accum.append(part)
        breadcrumbs.append({"name": part, "rel": str(Path(*accum))})
    parent_rel = str(Path(p).parent) if p else ""
    return TEMPLATES.TemplateResponse("files.html", {"request": request, "cwd_rel": p, "entries": entries, "breadcrumbs": breadcrumbs, "parent_rel": parent_rel})

@app.get("/admin/files/download")
def files_download(request: Request, p: str = Query(...)):
    login_required(request)
    path = safe_join(p)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Not a file")
    return FileResponse(str(path), filename=path.name)

@app.post("/admin/files/upload")
async def files_upload(request: Request, p: str = Form(""), file: UploadFile = File(...)):
    login_required(request)
    dest_dir = safe_join(p)
    if not dest_dir.is_dir():
        raise HTTPException(status_code=400, detail="Upload destination must be a directory")
    dest = dest_dir / Path(file.filename).name
    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)
    return RedirectResponse(url=f"/admin/files?p={p}", status_code=302)

@app.post("/admin/files/delete")
def files_delete(request: Request, p: str = Form(...)):
    login_required(request)
    path = safe_join(p)
    if path.is_file():
        path.unlink()
    else:
        raise HTTPException(status_code=400, detail="Deletion allowed only for files")
    parent = str(Path(p).parent) if p else ""
    return RedirectResponse(url=f"/admin/files?p={parent}", status_code=302)

@app.get("/project/{name}", response_class=HTMLResponse)
def project_page(request: Request, name: str):
    if not is_authed(request):
        return RedirectResponse(url="/login", status_code=302)
    proj_dir = safe_join(name)
    if not proj_dir.is_dir():
        raise HTTPException(status_code=404, detail="Project not found")
    run_exists = (proj_dir / "run.sh").exists()
    logs_dir = proj_dir / "logs"
    logs = []
    if logs_dir.exists():
        for lf in sorted(logs_dir.glob("*.log")):
            try:
                lm = datetime.fromtimestamp(lf.stat().st_mtime, tz=timezone.utc)
            except Exception:
                lm = None
            logs.append({"name": lf.name, "mtime": lm})
    return TEMPLATES.TemplateResponse("project.html", {"request": request, "project": {"name": name, "has_run": run_exists}, "logs": logs, "cwd_rel": name})

@app.post("/project/{name}/run")
def project_run(request: Request, name: str):
    login_required(request)
    proj_dir = safe_join(name)
    runfile = proj_dir / "run.sh"
    if not runfile.exists():
        raise HTTPException(status_code=400, detail="run.sh not found in project")
    try:
        subprocess.Popen(["bash", str(runfile)], cwd=str(proj_dir),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start: {e}")
    return RedirectResponse(url=f"/project/{name}", status_code=302)

def tail_bytes(path: Path, max_bytes: int = 64*1024) -> bytes:
    size = path.stat().st_size
    with open(path, "rb") as f:
        if size > max_bytes:
            f.seek(-max_bytes, os.SEEK_END)
        return f.read()

@app.get("/project/{name}/logs/{logname}")
def project_log(request: Request, name: str, logname: str, n: int = 200):
    login_required(request)
    proj_dir = safe_join(name)
    log_path = (proj_dir / "logs" / logname).resolve()
    try:
        log_path.relative_to(proj_dir / "logs")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid log path")
    if not log_path.is_file():
        raise HTTPException(status_code=404, detail="Log not found")
    data = tail_bytes(log_path)
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()[-n:]
    return PlainTextResponse("\n".join(lines))
PY

cat > "${APP_DIR}/app/templates/base.html" <<'HTML'
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Project Dashboard</title>
  <link rel="stylesheet" href="/static/style.css">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>nav form{display:inline}</style>
  <script>window.onload=function(){const path=location.pathname;if(path==='/login'){document.querySelector('input[name=username]')?.focus();}}</script>
  </head>
<body>
<nav>
  <a href="/">Dashboard</a>
  <a href="/admin/files">Files</a>
  <form action="/logout" method="post"><button>Logout</button></form>
  <div style="margin-left:auto;color:#9aa4ad;font-size:0.9em;">Project Dashboard</div>
 </nav>
<main>
  {% block content %}{% endblock %}
 </main>
</body>
</html>
HTML

cat > "${APP_DIR}/app/templates/login.html" <<'HTML'
{% extends "base.html" %}
{% block content %}
<h1>Login</h1>
<form method="post" action="/login">
  <label>Username <input name="username" autocomplete="username" required></label>
  <label>Password <input type="password" name="password" autocomplete="current-password" required></label>
  <button type="submit">Login</button>
 </form>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
{% endblock %}
HTML

cat > "${APP_DIR}/app/templates/dashboard.html" <<'HTML'
{% extends "base.html" %}
{% block content %}
<h1>Projects</h1>
<p>Root: {{ root }}</p>
<table>
  <thead><tr><th>Name</th><th>Last Modified</th><th>Run</th><th>Logs</th><th>Files</th></tr></thead>
  <tbody>
  {% for p in projects %}
    <tr>
      <td><a href="/project/{{ p.name }}">{{ p.name }}</a></td>
      <td>{{ p.last_modified.strftime("%Y-%m-%d %H:%M:%S %Z") }}</td>
      <td>{% if p.has_run %}<form method="post" action="/project/{{ p.name }}/run"><button>Run</button></form>{% else %}—{% endif %}</td>
      <td>{% if p.logs|length %}<a href="/project/{{ p.name }}">View</a>{% else %}—{% endif %}</td>
      <td><a href="/admin/files?p={{ p.name }}">Browse</a></td>
    </tr>
  {% endfor %}
  </tbody>
 </table>
{% if not projects %}<p>No projects found yet in {{ root }}.</p>{% endif %}
{% endblock %}
HTML

cat > "${APP_DIR}/app/templates/project.html" <<'HTML'
{% extends "base.html" %}
{% block content %}
<h1>Project: {{ project.name }}</h1>
<div class="actions">
  {% if project.has_run %}
  <form method="post" action="/project/{{ project.name }}/run"><button>Run run.sh</button></form>
  {% else %}
  <em>No run.sh found</em>
  {% endif %}
  <a class="btn" href="/admin/files?p={{ project.name }}">Open Files</a>
 </div>
<h2>Logs</h2>
<ul>
  {% for log in logs %}
    <li><a href="/project/{{ project.name }}/logs/{{ log.name }}" target="_blank">{{ log.name }}</a> — {{ log.mtime.strftime("%Y-%m-%d %H:%M:%S %Z") if log.mtime else "" }}</li>
  {% endfor %}
 </ul>
{% if not logs %}<p>No logs in logs/*.log</p>{% endif %}
{% endblock %}
HTML

cat > "${APP_DIR}/app/templates/files.html" <<'HTML'
{% extends "base.html" %}
{% block content %}
<h1>Files</h1>
<div class="breadcrumbs">
  <a href="/admin/files">/</a>
  {% for bc in breadcrumbs %} / <a href="/admin/files?p={{ bc.rel }}">{{ bc.name }}</a>{% endfor %}
 </div>

<form method="post" action="/admin/files/upload" enctype="multipart/form-data">
  <input type="hidden" name="p" value="{{ cwd_rel }}">
  <input type="file" name="file" required>
  <button type="submit">Upload</button>
 </form>

<table>
  <thead><tr><th>Name</th><th>Modified</th><th>Size</th><th>Actions</th></tr></thead>
  <tbody>
  {% if cwd_rel %}
    <tr><td colspan="4"><a href="/admin/files?p={{ parent_rel }}">⬆️ Up</a></td></tr>
  {% endif %}
  {% for e in entries %}
    <tr>
      <td>
        {% if e.is_dir %}
          📁 <a href="/admin/files?p={{ e.rel }}">{{ e.name }}</a>
        {% else %}
          📄 {{ e.name }}
        {% endif %}
      </td>
      <td>{{ e.mtime.strftime("%Y-%m-%d %H:%M:%S %Z") if e.mtime else "" }}</td>
      <td>{{ e.size if e.size else "" }}</td>
      <td>
        {% if not e.is_dir %}
          <a href="/admin/files/download?p={{ e.rel }}">Download</a>
          <form method="post" action="/admin/files/delete" style="display:inline" onsubmit="return confirm('Delete {{ e.name }}?')">
            <input type="hidden" name="p" value="{{ e.rel }}">
            <button>Delete</button>
          </form>
        {% endif %}
      </td>
    </tr>
  {% endfor %}
  </tbody>
 </table>
{% endblock %}
HTML

cat > "${APP_DIR}/app/static/style.css" <<'CSS'
:root { --bg:#0b0f14; --fg:#e6edf3; --muted:#9aa4ad; --accent:#7aa2f7; --panel:#111722; --border:#223; }
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--fg);font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,"Helvetica Neue",Arial}
nav{display:flex;gap:12px;align-items:center;background:var(--panel);padding:10px 14px;border-bottom:1px solid var(--border)}
nav a, nav button{color:var(--fg);text-decoration:none;background:#1a2230;border:1px solid var(--border);padding:6px 10px;border-radius:6px;cursor:pointer}
nav form{margin:0}
main{padding:16px;max-width:1100px;margin:0 auto}
h1,h2{margin:10px 0 12px 0}
table{width:100%;border-collapse:collapse;background:#0f1520;border:1px solid var(--border)}
th,td{padding:8px 10px;border-bottom:1px solid var(--border);vertical-align:top}
tr:nth-child(even){background:#0d131d}
.error{color:#ff6b6b}
form label{display:block;margin:8px 0}
input,button{font:inherit}
.btn{display:inline-block}
.breadcrumbs{margin-bottom:8px;color:var(--muted)}
CSS

echo "==> Creating Python venv and installing deps via uv"
uv venv "${APP_DIR}/.venv"
uv pip install -r "${APP_DIR}/requirements.txt" -p "${APP_DIR}/.venv/bin/python"

echo "==> Writing environment file"
cat > /etc/project-dashboard.env <<ENV
DASHBOARD_ROOT=${ROOT_DIR}
DASHBOARD_ADMIN_USER=admin
DASHBOARD_ADMIN_PASSWORD=admin
DASHBOARD_SECRET=$(openssl rand -hex 16)
ENV
chmod 600 /etc/project-dashboard.env

echo "==> Creating systemd service"
cat > /etc/systemd/system/project-dashboard.service <<SERVICE
[Unit]
Description=Project Dashboard (FastAPI)
After=network-online.target
Wants=network-online.target

[Service]
EnvironmentFile=/etc/project-dashboard.env
User=${REAL_USER}
Group=${REAL_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=2
KillSignal=SIGINT
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
SERVICE

echo "==> Configuring Nginx reverse proxy on :8080"
cat > /etc/nginx/sites-available/project-dashboard <<'NGINX'
server {
    listen 8080;
    server_name _;
    client_max_body_size 200m;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/project-dashboard /etc/nginx/sites-enabled/project-dashboard

echo "==> Enable and start services"
systemctl daemon-reload
systemctl enable --now project-dashboard
nginx -t && systemctl restart nginx

echo "==> Opening UFW port 8080 (if UFW is active)"
if ufw status 2>/dev/null | grep -q "Status: active"; then ufw allow 8080/tcp || true; fi

echo "==> Done"
echo "Test locally: curl -s http://127.0.0.1:8080/healthz"
echo "Then browse:  http://<EXTERNAL_IP>:8080  (login: admin/admin)"
