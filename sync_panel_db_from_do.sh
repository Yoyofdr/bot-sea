#!/usr/bin/env bash
set -euo pipefail

# Descarga una copia de la BD de DigitalOcean para alimentar el panel local.
# Seguridad: no modifica la BD remota; solo la copia por SSH/SCP.
#
# Uso:
#   chmod +x sync_panel_db_from_do.sh
#   DO_SSH="root@tu-servidor" \
#   DO_DB_PATH="/opt/seia/data/seia_monitor.db" \
#   ./sync_panel_db_from_do.sh

if [[ -z "${DO_SSH:-}" ]]; then
  echo "Error: define DO_SSH (ej: root@203.0.113.10)"
  exit 1
fi

if [[ -z "${DO_DB_PATH:-}" ]]; then
  echo "Error: define DO_DB_PATH (ruta remota al .db)"
  exit 1
fi

LOCAL_DIR="data"
LOCAL_DB="data/seia_monitor_panel.db"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
REMOTE_TMP="/tmp/seia_monitor_panel_copy_${TIMESTAMP}.db"

mkdir -p "${LOCAL_DIR}"

echo "[1/4] Validando acceso y existencia de DB remota..."
ssh "${DO_SSH}" "test -f \"${DO_DB_PATH}\" && ls -lh \"${DO_DB_PATH}\""

echo "[2/4] Creando copia temporal en DO (solo lectura sobre original)..."
ssh "${DO_SSH}" "cp \"${DO_DB_PATH}\" \"${REMOTE_TMP}\" && chmod 600 \"${REMOTE_TMP}\""

echo "[3/4] Descargando copia local para el panel..."
scp "${DO_SSH}:${REMOTE_TMP}" "${LOCAL_DB}"

echo "[4/4] Limpiando copia temporal en DO..."
ssh "${DO_SSH}" "rm -f \"${REMOTE_TMP}\""

echo "OK: copia panel disponible en ${LOCAL_DB}"
echo "Sugerencia: export PANEL_DB_PATH=${LOCAL_DB}"
