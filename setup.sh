#!/usr/bin/env bash
set -euo pipefail

APP_NAME="autotile"
SRC_SCRIPT="autotile.py"
BIN_DIR="${HOME}/.local/bin"
INSTALL_PATH="${BIN_DIR}/${APP_NAME}"
DESKTOP_DIR="${HOME}/.local/share/applications"
DESKTOP_FILE="${DESKTOP_DIR}/${APP_NAME}.desktop"

need_cmd() { command -v "$1" >/dev/null 2>&1; }

echo "==> Checking dependencies (wmctrl, xprop)…"
missing=()
need_cmd wmctrl || missing+=("wmctrl")
need_cmd xprop  || missing+=("x11-utils")

if [ ${#missing[@]} -gt 0 ]; then
  echo "==> Missing: ${missing[*]}"
  if need_cmd apt; then
    echo "==> Installing with apt (sudo required)…"
    sudo apt update
    sudo apt install -y wmctrl x11-utils x11-xserver-utils
  else
    echo "!! apt not found. Please install the above packages with your distro's package manager and re-run."
    exit 1
  fi
else
  echo "==> All dependencies present."
fi

echo "==> Installing ${APP_NAME} to ${INSTALL_PATH}"
mkdir -p "${BIN_DIR}"
if [ ! -f "${SRC_SCRIPT}" ]; then
  echo "!! ${SRC_SCRIPT} not found in current directory."
  exit 1
fi
install -m 0755 "${SRC_SCRIPT}" "${INSTALL_PATH}"

echo "==> Creating optional desktop launcher"
mkdir -p "${DESKTOP_DIR}"
cat > "${DESKTOP_FILE}" <<EOF
[Desktop Entry]
Name=AutoTile
Comment=Tile visible windows in a grid
Exec=${INSTALL_PATH}
Terminal=false
Type=Application
Categories=Utility;
EOF

echo "==> Done."
echo
echo "Use it now:"
echo "  ${APP_NAME}"
echo
echo "Add a hotkey in Cinnamon:"
echo "  System Settings → Keyboard → Shortcuts → Custom Shortcuts"
echo "  Command: ${INSTALL_PATH}"
echo "  Suggested: Super+T"
echo
echo "Uninstall:"
echo "  rm -f \"${INSTALL_PATH}\" \"${DESKTOP_FILE}\""
