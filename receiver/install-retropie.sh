#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/pip" install --upgrade pip
"$ROOT/.venv/bin/pip" install -r "$ROOT/receiver/requirements.txt"
if ! getent group input >/dev/null; then sudo groupadd input || true; fi
sudo usermod -a -G input "$USER" || true
cat <<SERVICE | sudo tee /etc/systemd/system/retropad.service >/dev/null
[Unit]
Description=RetroPad native receiver
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=$USER
WorkingDirectory=$ROOT
ExecStart=$ROOT/.venv/bin/python $ROOT/receiver/retropad_receiver.py --host 127.0.0.1:8080
Restart=always
RestartSec=2
[Install]
WantedBy=multi-user.target
SERVICE
sudo systemctl daemon-reload
sudo systemctl enable retropad.service
echo "RetroPad receiver service installed. Reboot after confirming the web server is also configured to start."
