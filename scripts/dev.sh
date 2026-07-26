#!/usr/bin/env bash
# scripts/dev.sh — DeviceLab hot-dev launcher
#
# Starts everything you need for local development in one command:
#   • Docker stack (DB + backend) with file-sync hot-reload
#   • Vite frontend dev server with HMR
#
# Usage:
#   ./scripts/dev.sh              normal start (uses cached images)
#   ./scripts/dev.sh --build      rebuild Docker images first
#   ./scripts/dev.sh --reset-db   wipe the DB volume and reseed
#   ./scripts/dev.sh --help

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# ── colours ────────────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'
  CYAN='\033[0;36m'; GREEN='\033[0;32m'
  YELLOW='\033[1;33m'; BLUE='\033[0;34m'; RED='\033[0;31m'
else
  BOLD=''; DIM=''; RESET=''; CYAN=''; GREEN=''; YELLOW=''; BLUE=''; RED=''
fi

banner()  { echo -e "\n${BOLD}${CYAN}$*${RESET}"; }
ok()      { echo -e "  ${GREEN}✓${RESET}  $*"; }
info()    { echo -e "  ${BLUE}→${RESET}  $*"; }
warn()    { echo -e "  ${YELLOW}⚠${RESET}  $*"; }
die()     { echo -e "  ${RED}✗${RESET}  $*" >&2; exit 1; }

# ── cleanup ─────────────────────────────────────────────────────────────────
FRONTEND_PID=""

cleanup() {
  echo ""
  warn "Shutting down DeviceLab..."
  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
    wait "$FRONTEND_PID" 2>/dev/null || true
  fi
  docker compose stop 2>/dev/null || true
  ok "All stopped. Bye!"
}
trap cleanup EXIT INT TERM

# ── banner ───────────────────────────────────────────────────────────────────
clear
echo -e "${BOLD}${CYAN}"
echo "  ██████╗ ███████╗██╗   ██╗██╗ ██████╗███████╗    ██╗      █████╗ ██████╗"
echo "  ██╔══██╗██╔════╝██║   ██║██║██╔════╝██╔════╝    ██║     ██╔══██╗██╔══██╗"
echo "  ██║  ██║█████╗  ██║   ██║██║██║     █████╗      ██║     ███████║██████╔╝"
echo "  ██║  ██║██╔══╝  ╚██╗ ██╔╝██║██║     ██╔══╝      ██║     ██╔══██║██╔══██╗"
echo "  ██████╔╝███████╗ ╚████╔╝ ██║╚██████╗███████╗    ███████╗██║  ██║██████╔╝"
echo "  ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝ ╚═════╝╚══════╝    ╚══════╝╚═╝  ╚═╝╚═════╝"
echo -e "${RESET}"

# ── args ─────────────────────────────────────────────────────────────────────
BUILD_FLAG=""
RESET_DB=false

for arg in "$@"; do
  case "$arg" in
    -b|--build)
      BUILD_FLAG="--build"
      ;;
    --reset-db)
      RESET_DB=true
      ;;
    -h|--help)
      echo "Usage: ./scripts/dev.sh [options]"
      echo ""
      echo "Options:"
      echo "  -b, --build    Force-rebuild Docker images before starting"
      echo "  --reset-db     Wipe volumes and re-seed the database from scratch"
      echo "  -h, --help     Show this help"
      echo ""
      echo "Hot-reload behaviour:"
      echo "  Python (.py)   → uvicorn detects the change and reloads in ~1 s"
      echo "  React  (.tsx)  → Vite HMR patches the browser instantly"
      echo "  pyproject.toml → Docker rebuilds the backend image automatically"
      echo "  New migration  → run:  docker compose restart prestart backend"
      exit 0
      ;;
    *)
      die "Unknown argument: $arg  (try --help)"
      ;;
  esac
done

# ── preflight ─────────────────────────────────────────────────────────────────
banner "Preflight"
command -v docker >/dev/null 2>&1 || die "docker not found — install Docker Desktop"
command -v bun    >/dev/null 2>&1 || die "bun not found — https://bun.sh"
ok "docker  $(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
ok "bun     $(bun --version)"
[[ -f .env ]] || warn ".env not found — copy .env.example and fill it in"

# ── optional db wipe ──────────────────────────────────────────────────────────
if $RESET_DB; then
  banner "Database reset"
  warn "Wiping Docker volumes..."
  docker compose down -v --remove-orphans 2>/dev/null || true
  ok "Volumes cleared — will re-seed on startup"
fi

# ── frontend deps (first run) ─────────────────────────────────────────────────
if [[ ! -d apps/web/node_modules ]]; then
  banner "Frontend setup"
  info "Installing node_modules (first run)..."
  (cd apps/web && bun install)
  ok "node_modules ready"
fi

# ── start frontend (background) ───────────────────────────────────────────────
banner "Starting services"
info "Frontend → Vite HMR  http://localhost:5173"
(
  cd apps/web
  bun run dev 2>&1 | while IFS= read -r line; do
    echo -e "  ${BLUE}[web]${RESET} ${DIM}$line${RESET}"
  done
) &
FRONTEND_PID=$!

# brief pause so Vite's startup noise lands before the Docker logs
sleep 1

# ── start docker stack ────────────────────────────────────────────────────────
if [[ -n "$BUILD_FLAG" ]]; then
  info "Backend  → rebuilding images..."
else
  info "Backend  → using cached images  (pass --build to force rebuild)"
fi

# ── urls summary ──────────────────────────────────────────────────────────────
echo ""
echo -e "  ${BOLD}Services${RESET}"
echo -e "  ${GREEN}▸${RESET} ${BOLD}Frontend${RESET}   http://localhost:5173    ${DIM}← start here${RESET}"
echo -e "  ${GREEN}▸${RESET} ${BOLD}API${RESET}        http://localhost:8000"
echo -e "  ${GREEN}▸${RESET} ${BOLD}Swagger${RESET}    http://localhost:8000/docs"
echo -e "  ${GREEN}▸${RESET} ${BOLD}Adminer${RESET}    http://localhost:8080    ${DIM}(DB browser)${RESET}"
echo ""
echo -e "  ${DIM}Save .py  → backend reloads in ~1 s${RESET}"
echo -e "  ${DIM}Save .tsx → browser updates instantly${RESET}"
echo -e "  ${DIM}Ctrl+C   → stops everything cleanly${RESET}"
echo ""
echo -e "${CYAN}${BOLD}─────────────────────────────── logs ──────────────────────────────${RESET}"
echo ""

docker compose up --watch $BUILD_FLAG
