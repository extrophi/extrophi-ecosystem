#!/usr/bin/env bash
set -euo pipefail

# Re-run with sudo if not root (needed for systemd/nginx/journalctl)
if [[ "${EUID}" -ne 0 ]]; then
  exec sudo -E bash "$0" "$@"
fi

echo "=== System Info ==="
uname -a || true
lsb_release -a 2>/dev/null || cat /etc/os-release || true
echo

APP_DIR="/opt/project-dashboard"
SITE_FILE="/etc/nginx/sites-available/project-dashboard"
ENV_FILE="/etc/project-dashboard.env"

echo "=== Paths ==="
echo "APP_DIR=${APP_DIR}"
echo "SITE_FILE=${SITE_FILE}"
echo "ENV_FILE=${ENV_FILE}"
echo

echo "=== App Directory Listing ==="
ls -la "${APP_DIR}" || echo "(missing)"
echo

echo "=== Python & Packages (venv) ==="
if [[ -x "${APP_DIR}/.venv/bin/python" ]]; then
  "${APP_DIR}/.venv/bin/python" -V || true
  "${APP_DIR}/.venv/bin/python" -c 'import fastapi,starlette,uvicorn,itsdangerous; print("fastapi=",fastapi.__version__); print("starlette=",starlette.__version__); import uvicorn as u; print("uvicorn=",u.__version__); import itsdangerous as d; print("itsdangerous=",d.__version__)' 2>/dev/null || true
else
  echo "Venv not found at ${APP_DIR}/.venv"
fi
echo

echo "=== Environment (redacted) ==="
if [[ -f "${ENV_FILE}" ]]; then
  sed -E 's/(DASHBOARD_ADMIN_PASSWORD=).*/\1***REDACTED***/; s/(DASHBOARD_SECRET=).*/\1***REDACTED***/' "${ENV_FILE}" || true
else
  echo "${ENV_FILE} (missing)"
fi
echo

echo "=== Service Status ==="
systemctl is-enabled project-dashboard || true
systemctl is-active project-dashboard || true
systemctl status project-dashboard --no-pager -l || true
echo

echo "=== Recent App Logs (last 200 lines) ==="
journalctl -u project-dashboard -n 200 --no-pager || true
echo

echo "=== Nginx Config Test ==="
nginx -t || true
echo

echo "=== Nginx Site Snippet ==="
if [[ -f "${SITE_FILE}" ]]; then
  sed -n '1,120p' "${SITE_FILE}"
else
  echo "${SITE_FILE} (missing)"
fi
echo

echo "=== Listening Ports (8001 app, 8080 nginx) ==="
ss -tlnp | egrep ':(8001|8080) ' || true
echo

echo "=== Health Checks ==="
curl -fsS http://127.0.0.1:8001/healthz || echo "(app not responding on 8001)"
echo
curl -fsS http://127.0.0.1:8080/healthz || echo "(nginx not responding on 8080)"
echo

echo "=== Done ==="
