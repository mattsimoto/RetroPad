# RetroPad

RetroPad turns phones and tablets into low-latency retro game controllers over a local network.

The project is designed around a single phone controller UI and a cross-platform receiver layer:

- macOS / OpenEmu: virtual HID work in progress, keyboard fallback available
- Linux / Raspberry Pi / RetroPie: `uinput` / `evdev` virtual gamepads
- Windows: virtual XInput gamepads with keyboard fallback
- Android / FullRoid: native bridge planned

## Current status

The current build supports:

- QR-code and six-character pairing
- up to four simultaneous phones as P1-P4
- controller profiles for NES, SNES, Genesis / Mega Drive, Game Boy, GBA, Nintendo 64, PlayStation, arcade, and generic gamepad
- analog and digital control events over local WebSockets
- responsive phone layouts with fullscreen support
- built-in QR generation with no npm dependency
- browser receiver / diagnostics page
- native Python receiver drivers

The immediate development target is reliable macOS HID enumeration so OpenEmu sees `RetroPad P1` as a real controller instead of only a keyboard.

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
       +-- macOS: virtual HID
       +-- Linux / Raspberry Pi: uinput / evdev
       +-- Windows: XInput
       +-- Android: native bridge planned
       v
OpenEmu / RetroArch / RetroPie / emulator
```

## Run the server

Requires Node.js 18+.

```bash
npm start
```

Open the receiver page on the gaming computer:

```text
http://localhost:8080/receiver.html
```

Scan the displayed QR code with a phone on the same local network.

## Run the native receiver

```bash
python3 -m pip install -r receiver/requirements.txt
```

Example:

```bash
python3 receiver/retropad_receiver.py \
  --host 127.0.0.1:8080 \
  --room ABC123 \
  --driver macos-hid
```

Replace `ABC123` with the current room code displayed by the browser receiver.

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
5. The emulator sees each phone as a normal local controller.
