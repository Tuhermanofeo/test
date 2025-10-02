#!/usr/bin/env bash
set -euo pipefail
# install_wrap.sh - Detecta Termux o Debian/Ubuntu y ejecuta el instalador apropiado

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

is_termux=false
if [ -n "${PREFIX-}" ] && echo "$PREFIX" | grep -q "com.termux"; then
  is_termux=true
fi
if [ -d "/data/data/com.termux" ]; then
  is_termux=true
fi

if $is_termux; then
  echo "Entorno: Termux detectado"
  bash "$SCRIPT_DIR/termux_install.sh"
else
  echo "Entorno: Linux (Debian/Ubuntu) detectado"
  bash "$SCRIPT_DIR/linux_install.sh"
fi

echo "Instalación finalizada. Revisa mensajes anteriores para errores."
