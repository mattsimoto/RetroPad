from .base import BaseDriver

try:
    from pynput.keyboard import Controller, Key
except ImportError as e:
    raise RuntimeError('pynput is required for the macOS OpenEmu driver') from e

# Each player gets a unique keyboard bank so OpenEmu can map multiple players.
# These are deliberately not tied to OpenEmu defaults: bind them once in
# OpenEmu > Settings/Preferences > Controls by clicking a control and pressing
# the matching RetroPad button on the phone.
PLAYER_MAPS = {
    1: {
        'UP': Key.up, 'DOWN': Key.down, 'LEFT': Key.left, 'RIGHT': Key.right,
        'A': 'd', 'B': 'f', 'X': 'e', 'Y': 'r',
        'C': 'g', 'Z': 'v',
        'C_UP': 'i', 'C_DOWN': 'k', 'C_LEFT': 'j', 'C_RIGHT': 'l',
        'CROSS': 'd', 'CIRCLE': 'f', 'SQUARE': 'r', 'TRIANGLE': 'e',
        'L': 'q', 'R': 'w', 'L1': 'q', 'R1': 'w', 'L2': 'a', 'R2': 's',
        'START': Key.enter, 'SELECT': Key.shift_r, 'MODE': Key.tab,
        '1': 'd', '2': 'f', '3': 'g', '4': 'r', '5': 'e', '6': 't', 'COIN': '5',
    },
    2: {
        'UP': '8', 'DOWN': '5', 'LEFT': '4', 'RIGHT': '6',
        'A': 'p', 'B': 'o', 'X': '0', 'Y': '9',
        'C': '[', 'Z': ']', 'C_UP': 'u', 'C_DOWN': 'm', 'C_LEFT': 'n', 'C_RIGHT': ',',
        'CROSS': 'p', 'CIRCLE': 'o', 'SQUARE': '9', 'TRIANGLE': '0',
        'L': '7', 'R': '-', 'L1': '7', 'R1': '-', 'L2': 'y', 'R2': '=',
        'START': '\\', 'SELECT': ';', 'MODE': "'",
        '1': 'p', '2': 'o', '3': '[', '4': '9', '5': '0', '6': ']', 'COIN': '6',
    },
    3: {
        'UP': 't', 'DOWN': 'g', 'LEFT': 'f', 'RIGHT': 'h',
        'A': 'b', 'B': 'n', 'X': 'v', 'Y': 'c',
        'C': 'm', 'Z': 'x', 'C_UP': 'r', 'C_DOWN': 'y', 'C_LEFT': 'e', 'C_RIGHT': 'u',
        'CROSS': 'b', 'CIRCLE': 'n', 'SQUARE': 'c', 'TRIANGLE': 'v',
        'L': 'z', 'R': 'j', 'L1': 'z', 'R1': 'j', 'L2': '1', 'R2': '2',
        'START': '3', 'SELECT': '4', 'MODE': '5',
        '1': 'b', '2': 'n', '3': 'm', '4': 'c', '5': 'v', '6': 'x', 'COIN': '7',
    },
    4: {
        'UP': 'w', 'DOWN': 's', 'LEFT': 'a', 'RIGHT': 'd',
        'A': 'k', 'B': 'l', 'X': 'i', 'Y': 'o',
        'C': '.', 'Z': '/', 'C_UP': 'q', 'C_DOWN': 'z', 'C_LEFT': 'x', 'C_RIGHT': 'c',
        'CROSS': 'k', 'CIRCLE': 'l', 'SQUARE': 'o', 'TRIANGLE': 'i',
        'L': 'u', 'R': 'p', 'L1': 'u', 'R1': 'p', 'L2': ',', 'R2': '.',
        'START': '0', 'SELECT': '-', 'MODE': '=',
        '1': 'k', '2': 'l', '3': '/', '4': 'o', '5': 'i', '6': '.', 'COIN': '8',
    },
}


class MacOSOpenEmuDriver(BaseDriver):
    name = 'macOS OpenEmu keyboard bridge'

    def __init__(self):
        super().__init__()
        self.k = Controller()
        self.held = set()
        print('macOS note: current macOS restricts third-party virtual HID creation.')
        print('Using OpenEmu keyboard bridge. In OpenEmu Controls, keep Input = Keyboard')
        print('and bind each control by clicking it, then pressing that RetroPad button.')

    def _key(self, player, button):
        return PLAYER_MAPS.get(player, PLAYER_MAPS[1]).get(button)

    def button(self, player, button, pressed):
        key = self._key(player, button)
        if key is None:
            return
        token = (player, button)
        if pressed and token not in self.held:
            self.k.press(key)
            self.held.add(token)
        elif not pressed and token in self.held:
            self.k.release(key)
            self.held.remove(token)

    def axis(self, player, axis, x, y):
        if axis != 'left':
            return
        self.button(player, 'LEFT', x < -0.45)
        self.button(player, 'RIGHT', x > 0.45)
        self.button(player, 'UP', y < -0.45)
        self.button(player, 'DOWN', y > 0.45)

    def release_all(self):
        for player, button in list(self.held):
            key = self._key(player, button)
            if key is not None:
                try:
                    self.k.release(key)
                except Exception:
                    pass
        self.held.clear()
