# Architecture

RetroPad separates the phone UI from the platform-specific input driver.

```text
Phone / tablet
    |
    | WebSocket over LAN
    v
Node relay server
    |
    +--> browser diagnostics receiver
    |
    v
Python native receiver
    |
    +--> macOS HID backend
    +--> Linux uinput backend
    +--> Windows vgamepad backend
    +--> keyboard fallback
```

The network protocol stays platform-neutral. Console profiles affect the phone layout and button semantics, while the host driver translates those events into the input system expected by the emulator.

The design goal is eventually to package the server and native receiver together so users launch one RetroPad application, scan one QR code, and play without terminal setup.
