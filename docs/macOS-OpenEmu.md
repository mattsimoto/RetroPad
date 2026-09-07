# macOS / OpenEmu

## Why the first approaches failed

RetroPad's network and pairing path works on macOS, but two different input approaches proved unsuitable for OpenEmu:

1. Direct `IOHIDUserDevice` creation is blocked on current macOS without Apple's virtual-HID/DriverKit entitlements.
2. `pynput`/synthetic keyboard events can register while assigning OpenEmu controls but may not be delivered to a running emulated game.

The current macOS path therefore uses the signed **Karabiner-DriverKit-VirtualHIDDevice** project as the hardware-level keyboard layer. Its virtual keyboard is recognized by macOS like physical hardware. RetroPad talks to its daemon through a small client bridge.

## Setup

From the RetroPad repository:

```bash
bash scripts/macos/setup-karabiner.sh
```

The script will:

- download/open the latest signed Karabiner VirtualHIDDevice package if it is not installed;
- activate the DriverKit extension;
- clone the official client source used to communicate with the daemon;
- install XcodeGen through an existing Homebrew installation if needed;
- build `receiver/bin/retropad-karabiner-bridge`;
- start the Karabiner VirtualHIDDevice daemon.

The official Karabiner client requires root privileges to send events, so the RetroPad driver launches the small bridge through `sudo`. You may be prompted for your macOS password in Terminal.

Do not disable SIP or weaken macOS security for RetroPad.

## Run

Start the server:

```bash
npm start
```

Then, in another Terminal window:

```bash
python3 receiver/retropad_receiver.py \
  --host 127.0.0.1:8080 \
  --room ABC123 \
  --driver macos-karabiner
```

Replace `ABC123` with the room code shown on the RetroPad receiver page.

Expected driver line:

```text
Driver:   macOS Karabiner hardware keyboard bridge
```

## OpenEmu mapping

OpenEmu will still show **Keyboard** as the input source. That is intentional. The difference is that the key events now originate from a DriverKit virtual keyboard rather than from app-level synthetic keystrokes.

Map each OpenEmu control once by clicking the field and tapping the corresponding RetroPad button. Then launch a game and verify the same button works during gameplay.

## Notes

- P1-P4 use separate keyboard-key banks so multiple phones can be mapped independently.
- Analog sticks are converted to digital directions for the OpenEmu keyboard path. Native analog gamepad output remains a future macOS target.
- `macos-openemu` remains available as a fallback/debug mode, but `macos-karabiner` is the preferred OpenEmu driver.

## Upstream dependency

RetroPad does not redistribute Karabiner's signed DriverKit package. The setup script retrieves it from the official `pqrs-org/Karabiner-DriverKit-VirtualHIDDevice` GitHub releases and builds only RetroPad's small client bridge locally.
