#!/bin/bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This setup script is for macOS only."
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEPS="$ROOT/.deps/Karabiner-DriverKit-VirtualHIDDevice"
BIN_DIR="$ROOT/receiver/bin"
HELPER_SRC="$ROOT/receiver/macos/retropad_karabiner_bridge.cpp"
MANAGER="/Applications/.Karabiner-VirtualHIDDevice-Manager.app/Contents/MacOS/Karabiner-VirtualHIDDevice-Manager"
DAEMON="/Library/Application Support/org.pqrs/Karabiner-DriverKit-VirtualHIDDevice/Applications/Karabiner-VirtualHIDDevice-Daemon.app/Contents/MacOS/Karabiner-VirtualHIDDevice-Daemon"

mkdir -p "$ROOT/.deps" "$BIN_DIR"

echo "RetroPad macOS hardware-input setup"
echo "------------------------------------"

if [[ ! -x "$MANAGER" ]]; then
  echo "Karabiner DriverKit VirtualHIDDevice is not installed."
  echo "Downloading the latest signed package from pqrs-org..."
  PKG="$(python3 - <<'PY'
import json, tempfile, urllib.request, os
api='https://api.github.com/repos/pqrs-org/Karabiner-DriverKit-VirtualHIDDevice/releases/latest'
with urllib.request.urlopen(api) as r: data=json.load(r)
asset=next(a for a in data['assets'] if a['name'].endswith('.pkg'))
out=os.path.join(tempfile.gettempdir(), asset['name'])
urllib.request.urlretrieve(asset['browser_download_url'], out)
print(out)
PY
)"
  echo "Opening installer: $PKG"
  open "$PKG"
  echo
  read -r -p "Finish the macOS installer, then press Return here... " _
fi

if [[ ! -x "$MANAGER" ]]; then
  echo "Karabiner VirtualHIDDevice still is not installed. Run this script again after installation."
  exit 2
fi

echo "Activating signed DriverKit extension..."
"$MANAGER" activate || true

if [[ ! -d "$DEPS/.git" ]]; then
  echo "Fetching the official Karabiner VirtualHIDDevice client headers..."
  git clone --depth 1 https://github.com/pqrs-org/Karabiner-DriverKit-VirtualHIDDevice.git "$DEPS"
else
  echo "Updating Karabiner client source..."
  git -C "$DEPS" pull --ff-only || true
fi

if ! command -v xcodegen >/dev/null 2>&1; then
  BREW="$(command -v brew || true)"
  [[ -z "$BREW" && -x /usr/local/bin/brew ]] && BREW=/usr/local/bin/brew
  [[ -z "$BREW" && -x /opt/homebrew/bin/brew ]] && BREW=/opt/homebrew/bin/brew
  if [[ -n "$BREW" ]]; then
    echo "Installing XcodeGen with Homebrew..."
    "$BREW" install xcodegen
  else
    echo "XcodeGen is required to build the small RetroPad client bridge."
    echo "Install Homebrew/XcodeGen, then run this script again."
    echo "XcodeGen: https://github.com/yonaskolb/XcodeGen"
    exit 3
  fi
fi

EXAMPLE="$DEPS/examples/virtual-hid-device-service-client"
cp "$HELPER_SRC" "$EXAMPLE/src/main.cpp"

echo "Building RetroPad Karabiner bridge..."
(
  cd "$EXAMPLE"
  make clean >/dev/null 2>&1 || true
  make
)
cp "$EXAMPLE/build/Release/virtual-hid-device-service-client" "$BIN_DIR/retropad-karabiner-bridge"
chmod +x "$BIN_DIR/retropad-karabiner-bridge"

echo "Starting Karabiner VirtualHIDDevice daemon..."
sudo -v
if ! pgrep -f 'Karabiner-VirtualHIDDevice-Daemon' >/dev/null 2>&1; then
  sudo "$DAEMON" >/tmp/retropad-karabiner-daemon.log 2>&1 &
  sleep 2
fi

echo
echo "Setup complete."
echo "RetroPad bridge: $BIN_DIR/retropad-karabiner-bridge"
echo "Daemon log: /tmp/retropad-karabiner-daemon.log"
echo
echo "Next, run the RetroPad receiver with:"
echo "  python3 receiver/retropad_receiver.py --room YOURCODE --driver macos-karabiner"
