# macOS / OpenEmu status

Current target: make OpenEmu enumerate `RetroPad P1` as a real HID gamepad.

## What already works

- Phone pairs with the RetroPad server.
- Input packets reach the native receiver.
- The macOS helper compiles with current Command Line Tools by resolving `IOHIDUserDevice` symbols dynamically from IOKit.
- The receiver creates Player 1 immediately and sends a neutral report so enumeration can happen before the first phone input.

## Current blocker

OpenEmu still reports only `Keyboard` / `No available controllers` on the test Mac even when the receiver reports that the macOS HID backend is running.

## Next diagnostics

1. Confirm whether the virtual device appears in the macOS IORegistry / HID device list outside OpenEmu.
2. If it appears there, inspect the HID descriptor and OpenEmu matching behavior.
3. If it does not appear there, replace the current `IOHIDUserDevice` approach with a supported modern macOS virtual-controller path rather than weakening system security.

Do not require disabling SIP or other macOS protections as part of normal installation.
