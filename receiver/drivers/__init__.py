import platform

def create_driver(choice="auto"):
    system=platform.system().lower()
    if choice in ("auto","macos-hid") and system=="darwin":
        try:
            from .macos_hid import MacOSHIDDriver
            return MacOSHIDDriver()
        except Exception as e:
            if choice=="macos-hid": raise
            print(f"macOS virtual HID unavailable ({e}); using keyboard fallback.")
    if choice in ("auto","linux-uinput") and system=="linux":
        try:
            from .linux_uinput import LinuxUInputDriver
            return LinuxUInputDriver()
        except Exception as e:
            if choice=="linux-uinput": raise
            print(f"Linux virtual gamepad unavailable ({e}); using keyboard fallback.")
    if choice in ("auto","windows-vgamepad") and system=="windows":
        try:
            from .windows_vgamepad import WindowsVGamepadDriver
            return WindowsVGamepadDriver()
        except Exception as e:
            if choice=="windows-vgamepad": raise
            print(f"Windows virtual gamepad unavailable ({e}); using keyboard fallback.")
    from .keyboard import KeyboardDriver
    return KeyboardDriver()
