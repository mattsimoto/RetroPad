import platform


def create_driver(choice="auto"):
    system = platform.system().lower()

    if system == "darwin":
        if choice == "macos-hid":
            raise RuntimeError(
                "Direct macOS virtual HID creation is restricted by Apple entitlement requirements. "
                "Use --driver macos-openemu for OpenEmu, or --driver keyboard for generic keyboard fallback."
            )
        if choice in ("auto", "macos-openemu"):
            from .macos_openemu import MacOSOpenEmuDriver
            return MacOSOpenEmuDriver()

    if choice in ("auto", "linux-uinput") and system == "linux":
        try:
            from .linux_uinput import LinuxUInputDriver
            return LinuxUInputDriver()
        except Exception as e:
            if choice == "linux-uinput":
                raise
            print(f"Linux virtual gamepad unavailable ({e}); using keyboard fallback.")

    if choice in ("auto", "windows-vgamepad") and system == "windows":
        try:
            from .windows_vgamepad import WindowsVGamepadDriver
            return WindowsVGamepadDriver()
        except Exception as e:
            if choice == "windows-vgamepad":
                raise
            print(f"Windows virtual gamepad unavailable ({e}); using keyboard fallback.")

    from .keyboard import KeyboardDriver
    return KeyboardDriver()
