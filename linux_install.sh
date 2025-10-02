#!/usr/bin/env bash
set -euo pipefail
# linux_install.sh - Instalador para Debian/Ubuntu

## CONFIGURACIÓN RÁPIDA
PYTHON_BIN=python3
VENV_DIR="$HOME/osint_venv"
PROJECT_DIR="$HOME/osint_tool"
REQUIREMENTS_FILE="requirements.txt"

echo "Actualizando repositorios..."
sudo apt-get update

echo "Instalando dependencias del sistema..."
sudo apt-get install -y build-essential pkg-config git curl wget \
    python3-pip python3-venv python3-dev libffi-dev libssl-dev \
    tesseract-ocr tesseract-ocr-eng poppler-utils tor

# Opcionales útiles
sudo apt-get install -y imagemagick exiftool

echo "Creando carpeta del proyecto en $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

cat > "$REQUIREMENTS_FILE" <<'EOF'
requests
beautifulsoup4
python-whois
dnspython
tldextract
pyyaml
cryptography
networkx
matplotlib
pillow
pytesseract
PyPDF2
exifread
shodan
EOF

echo "Creando virtualenv en $VENV_DIR (usarás pip dentro de este)..."
$PYTHON_BIN -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "Actualizando pip..."
pip install --upgrade pip

echo "Instalando dependencias Python (esto puede tardar)..."
pip install -r "$REQUIREMENTS_FILE" || {
  echo "Falló pip install - comprobando instalación parcial..."
  pip install --upgrade pip setuptools wheel
  pip install -r "$REQUIREMENTS_FILE"
}

# Copiar/crear archivos base: config.yaml y plantilla osint_tool.py si no existen
if [ ! -f config.yaml ]; then
  cat > config.yaml <<'YAML'
user_agents:
  - "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36"
use_tor: false
rate_limit_seconds: 1.5
shodan_api_key: ""
ip_info_token: ""
output_dir: "osint_output"
encrypt_results: false
encryption_key: ""
YAML
  echo "Archivo config.yaml creado. Edita las API keys según necesites."
fi

if [ ! -f osint_tool.py ]; then
  echo "No se detectó osint_tool.py en $PROJECT_DIR. Si quieres que cree el script, ejecuta: ./create_script.sh"
fi

echo "Comandos útiles:"
echo "  source $VENV_DIR/bin/activate   # activar virtualenv"
echo "  python osint_tool.py --help     # ver opciones del script"
echo "  tor &                           # iniciar tor si quieres usar --use-tor"
echo
echo "Instalación en Linux completada."
