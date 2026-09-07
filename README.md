# RetroPad

RetroPad turns phones and tablets into low-latency retro game controllers over a local network.

The project uses one phone controller UI and a cross-platform native receiver layer:

- macOS / OpenEmu: Karabiner DriverKit hardware-level virtual keyboard bridge
- Linux / Raspberry Pi / RetroPie: `uinput` / `evdev` virtual gamepads
- Windows: virtual XInput gamepads with keyboard fallback
- Android / FullRoid: native bridge planned

## Current status

RetroPad currently supports:

- QR-code and six-character pairing
- up to four simultaneous phones as P1-P4
- controller profiles for NES, SNES, Genesis / Mega Drive, Game Boy, GBA, Nintendo 64, PlayStation, arcade, and generic gamepad
- analog and digital control events over local WebSockets
- responsive phone layouts with fullscreen support
- browser receiver / diagnostics page
- native Python receiver drivers

## Architecture

```text
Phone / tablet PWA
       |
       | local WebSocket
       v
RetroPad server
       |
       v
Native receiver
       |
       +-- macOS: Karabiner DriverKit virtual keyboard
       +-- Linux / Raspberry Pi: uinput / evdev
       +-- Windows: XInput
       +-- Android: native bridge planned
       v
OpenEmu / RetroArch / RetroPie / emulator
```

## Install and run

Requires Node.js 18+ and Python 3.

```bash
git clone https://github.com/mattsimoto/RetroPad.git
cd RetroPad
npm install
python3 -m pip install -r receiver/requirements.txt
npm start
```

Open the receiver page on the gaming computer:

```text
http://localhost:8080/receiver.html
```

Scan the displayed QR code with a phone on the same local network.

## macOS / OpenEmu

Synthetic keyboard injection can register while assigning OpenEmu controls but fail inside a running game. RetroPad therefore uses the signed Karabiner DriverKit VirtualHIDDevice as its preferred macOS input path.

One-time setup:

```bash
bash scripts/macos/setup-karabiner.sh
```

Then run:

```bash
python3 receiver/retropad_receiver.py \
  --host 127.0.0.1:8080 \
  --room ABC123 \
  --driver macos-karabiner
```

Replace `ABC123` with the room code displayed by the browser receiver.

See `docs/macOS-OpenEmu.md` for details.

## Linux / Raspberry Pi

Use the native uinput receiver:

```bash
python3 receiver/retropad_receiver.py --room ABC123 --driver linux-uinput
```

RetroPie and RetroArch can then map the generated virtual gamepad like a normal local controller.

## Windows

Use the native virtual gamepad receiver:

```bash
python receiver/retropad_receiver.py --room ABC123 --driver windows-vgamepad
```

## Development

```bash
npm test
python3 -m py_compile receiver/retropad_receiver.py receiver/drivers/*.py
```

## Project direction

The finished experience should require no account, cloud service, Bluetooth pairing menu, or IP-address entry. The target flow is:

1. Start RetroPad Receiver.
2. Scan a QR code.
3. Phone becomes P1.
4. Additional phones become P2-P4.
5. The emulator receives each phone as usable local input.
