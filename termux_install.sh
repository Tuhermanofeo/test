#!/usr/bin/env bash
set -euo pipefail
# termux_install.sh - Instalador para Termux (Android)
PROJECT_DIR="$HOME/osint_tool"
VENV_DIR="$HOME/osint_venv"
REQUIREMENTS_FILE="requirements.txt"

echo "Actualizando repositorios pkg..."
pkg update -y
pkg upgrade -y

echo "Instalando herramientas base en Termux..."
pkg install -y git python clang make pkg-config openssl-tool libcrypt-dev \
    libffi-dev wget curl proot-distro

# Intentamos instalar tesseract en Termux; puede no estar disponible en todos los mirrors
echo "Instalando tesseract (si está disponible)..."
if pkg search tesseract | grep -q tesseract; then
  pkg install -y tesseract
else
  echo "Paquete tesseract no encontrado en este repositorio Termux. Considera usar proot-distro (Debian/Ubuntu)."
fi

echo "Instalando pip y creando virtualenv..."
python -m pip install --upgrade pip
python -m pip install virtualenv
python -m virtualenv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

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

echo "Instalando dependencias Python (esto puede tardar y algunos paquetes pueden fallar en Termux)..."
pip install --upgrade pip setuptools wheel
pip install -r "$REQUIREMENTS_FILE" || {
  echo "Algunos paquetes fallaron al compilar en Termux. Recomendado: usar proot-distro para un entorno Debian completo:"
  echo "  proot-distro install debian"
  echo "  proot-distro login debian --shared-tmp"
  echo "Y luego ejecutar el script de instalación para Debian dentro del proot."
}

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

if [ ! -f config.yaml ]; then
  cat > config.yaml <<'YAML'
user_agents:
  - "Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Mobile"
use_tor: false
rate_limit_seconds: 1.5
shodan_api_key: ""
ip_info_token: ""
output_dir: "osint_output"
encrypt_results: false
encryption_key: ""
YAML
  echo "config.yaml creado en $PROJECT_DIR"
fi

echo "Instalación en Termux finalizada."
echo "Si ves errores con pytesseract/cryptography/matplotlib, usa proot-distro (Debian) para mayor compatibilidad:"
echo "  proot-distro install debian"
echo "  proot-distro login debian"
echo "  luego ejecuta /path/to/install_wrap.sh dentro del proot"
