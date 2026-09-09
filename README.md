# RetroPad

RetroPad turns an Android phone running a retro-gaming suite such as FullRoid into a console for a larger screen.

## v0.4 project scope

The Android phone is the gaming system. The Mac, PC, or smart TV is only a low-latency display target.

```text
Android phone
├── FullRoid / emulator
├── ROM + game state
├── RetroPad native Android companion
│   ├── controller overlay
│   ├── screen/audio capture
│   └── WebRTC sender
│
└──────── local Wi-Fi / WebRTC ────────>

Mac / PC / TV
└── RetroPad Display
    ├── QR pairing
    └── low-latency game video/audio
```

The target experience is:

1. Open RetroPad Display on a Mac, PC, or TV.
2. A QR code appears.
3. Scan it with the RetroPad Android companion.
4. Launch a ROM in FullRoid.
5. The game appears on the larger display.
6. The phone shows a console-specific controller layout and remains the controller.

## Why the scope changed

Earlier prototypes made the phone a remote controller for an emulator running on Windows or macOS. That required platform-specific virtual-controller drivers and created unnecessary complexity.

In v0.4, FullRoid stays responsible for emulation. RetroPad focuses on display streaming, pairing, and controller UX.

## Current v0.4 work

- WebRTC signaling through the RetroPad Node server
- browser-based display receiver for Mac/PC/TV
- QR room pairing
- native Android companion architecture
- console-specific controller profiles
- local-network-first design

## Legacy prototype

The existing `public/` controller UI and `receiver/` native drivers are retained temporarily as reference from v0.3.x. They are no longer the primary architecture.

## Run the display server

Requires Node.js 18+.

```bash
git clone https://github.com/mattsimoto/RetroPad.git
cd RetroPad
npm install
npm start
```

Then open:

```text
http://localhost:8080/display.html
```

The display page creates a six-character room and QR pairing code.

## Development roadmap

### Milestone 1 — Display receiver
- QR pairing
- WebRTC offer/answer/ICE signaling
- fullscreen video playback
- reconnect state

### Milestone 2 — Android companion
- native Android project
- MediaProjection screen capture
- hardware video encoding
- WebRTC sender
- QR scanner

### Milestone 3 — FullRoid control integration
- determine the most reliable Android input path supported by FullRoid
- console-aware layouts for NES, SNES, Genesis, N64, GameCube, PlayStation, PS2, and arcade
- input latency tuning

### Milestone 4 — TV targets
- browser-capable smart TVs
- Android TV / Google TV receiver
- optional Google Cast support

## Design principles

- No account required.
- Local network first.
- ROMs and game state remain on the phone.
- The display device should not need an emulator.
- QR pairing should be the default setup path.
- Gaming latency takes priority over visual polish.
