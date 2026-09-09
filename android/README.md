# RetroPad Android companion

This directory is the home of the v0.4 native Android app.

## Role

The Android app will run alongside FullRoid and provide:

- QR pairing to a RetroPad Display
- MediaProjection screen capture
- WebRTC video/audio sender
- console-specific controller UI
- FullRoid input integration

## First implementation target

The first Android milestone is deliberately narrow:

1. Scan a `retropad://pair?...` QR code.
2. Ask the user for Android screen-capture permission.
3. Capture the phone screen with MediaProjection.
4. Create a WebRTC peer connection.
5. Send the captured video to the browser display.
6. Maintain a foreground notification while streaming.

Controller injection into FullRoid comes after this video path works reliably.

## Recommended Android baseline

- Kotlin
- minSdk 29 or newer for the initial prototype
- target current Android SDK
- Jetpack Compose for the controller UI
- AndroidX Activity/Compose
- Google WebRTC/native WebRTC package or a maintained compatible distribution
- CameraX/ML Kit or ZXing for QR scanning

## Acceptance test

On the Galaxy S22 Ultra:

1. Open RetroPad Display on a PC/Mac.
2. Scan its QR code.
3. Approve screen capture.
4. Open FullRoid and launch a game.
5. The game appears fullscreen on the PC/Mac with usable frame rate and low latency.

That test must pass before building the FullRoid control-injection layer.
