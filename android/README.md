# RetroPad Android companion

This directory contains the v0.4 native Android companion. In the new architecture, the Android phone is the game system and the Mac/PC/TV is only the display.

## Alpha 1 acceptance test

1. Start RetroPad on a Mac or PC with `npm start`.
2. Open `http://localhost:8080/display.html`.
3. Install the debug APK produced by the `Build Android APK` GitHub Actions workflow.
4. Scan the QR code on the display.
5. Android should offer to open the `retropad://pair` link with RetroPad.
6. Tap **Start Cast**.
7. Approve Android's screen-sharing prompt.
8. The phone screen should appear in the browser display over the local network.
9. Open FullRoid and launch a game. The game should remain visible on the paired display.

## Implemented in Alpha 1

- `retropad://pair` deep-link registration
- display host, port, and room parsing from the QR code
- Android signaling peer over the existing RetroPad WebSocket server
- Android MediaProjection screen-capture permission
- foreground media-projection service required by modern Android
- WebRTC screen video track
- WebRTC offer/answer/ICE signaling through RetroPad
- direct local WebRTC video delivery to the browser display

## Not implemented yet

- FullRoid controller-input injection
- game audio capture
- automatic orientation/resolution renegotiation
- TURN relay for non-local networks
- production signing / Play Store packaging
- controller overlays

## Build locally

Open the `android` directory in Android Studio, or run the GitHub Actions workflow. The project uses Kotlin, minSdk 29, target/compile SDK 35, OkHttp WebSockets, and the maintained `io.github.webrtc-sdk:android` WebRTC package.

The next milestone after screen casting works is determining the cleanest Android input path that FullRoid accepts while FullRoid remains the foreground emulator.
