import subprocess
import time
from pathlib import Path
from .base import BaseDriver

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / 'bin' / 'retropad-karabiner-bridge'

# USB HID keyboard usages. These are intentionally simple keyboard keys because
# OpenEmu already supports keyboard bindings; Karabiner makes them arrive as
# hardware-level virtual keyboard events instead of app-synthesized events.
PLAYER_MAPS = {
    1: {
        'UP':0x52,'DOWN':0x51,'LEFT':0x50,'RIGHT':0x4f,
        'A':0x07,'B':0x09,'X':0x08,'Y':0x15,'C':0x0a,'Z':0x19,
        'C_UP':0x0c,'C_DOWN':0x0e,'C_LEFT':0x0d,'C_RIGHT':0x0f,
        'CROSS':0x07,'CIRCLE':0x09,'SQUARE':0x15,'TRIANGLE':0x08,
        'L':0x14,'R':0x1a,'L1':0x14,'R1':0x1a,'L2':0x04,'R2':0x16,
        'START':0x28,'SELECT':0x2c,'MODE':0x2b,
        '1':0x07,'2':0x09,'3':0x0a,'4':0x15,'5':0x08,'6':0x17,'COIN':0x22,
    },
    2: {
        'UP':0x1e,'DOWN':0x1f,'LEFT':0x20,'RIGHT':0x21,
        'A':0x13,'B':0x12,'X':0x27,'Y':0x26,'C':0x2f,'Z':0x30,
        'C_UP':0x18,'C_DOWN':0x10,'C_LEFT':0x11,'C_RIGHT':0x36,
        'CROSS':0x13,'CIRCLE':0x12,'SQUARE':0x26,'TRIANGLE':0x27,
        'L':0x24,'R':0x2d,'L1':0x24,'R1':0x2d,'L2':0x1c,'R2':0x2e,
        'START':0x31,'SELECT':0x33,'MODE':0x34,
        '1':0x13,'2':0x12,'3':0x2f,'4':0x26,'5':0x27,'6':0x30,'COIN':0x23,
    },
    3: {
        'UP':0x17,'DOWN':0x0a,'LEFT':0x09,'RIGHT':0x0b,
        'A':0x05,'B':0x11,'X':0x19,'Y':0x06,'C':0x10,'Z':0x1b,
        'C_UP':0x15,'C_DOWN':0x1c,'C_LEFT':0x08,'C_RIGHT':0x18,
        'CROSS':0x05,'CIRCLE':0x11,'SQUARE':0x06,'TRIANGLE':0x19,
        'L':0x1d,'R':0x0d,'L1':0x1d,'R1':0x0d,'L2':0x1e,'R2':0x1f,
        'START':0x20,'SELECT':0x21,'MODE':0x22,
        '1':0x05,'2':0x11,'3':0x10,'4':0x06,'5':0x19,'6':0x1b,'COIN':0x24,
    },
    4: {
        'UP':0x1a,'DOWN':0x16,'LEFT':0x04,'RIGHT':0x07,
        'A':0x0e,'B':0x0f,'X':0x0c,'Y':0x12,'C':0x37,'Z':0x38,
        'C_UP':0x14,'C_DOWN':0x1d,'C_LEFT':0x1b,'C_RIGHT':0x06,
        'CROSS':0x0e,'CIRCLE':0x0f,'SQUARE':0x12,'TRIANGLE':0x0c,
        'L':0x18,'R':0x13,'L1':0x18,'R1':0x13,'L2':0x36,'R2':0x37,
        'START':0x27,'SELECT':0x2d,'MODE':0x2e,
        '1':0x0e,'2':0x0f,'3':0x38,'4':0x12,'5':0x0c,'6':0x37,'COIN':0x25,
    },
}

class MacOSKarabinerDriver(BaseDriver):
    name = 'macOS Karabiner hardware keyboard bridge'

    def __init__(self):
        super().__init__()
        if not BIN.exists():
            raise RuntimeError('Karabiner bridge is not built. Run: bash scripts/macos/setup-karabiner.sh')
        self.held = set()
        # The official Karabiner client must run as root. sudo uses the current
        # controlling terminal for the password prompt while stdin remains ours.
        self.proc = subprocess.Popen(
            ['sudo', str(BIN)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            bufsize=1,
        )
        self._wait_ready()
        print('Karabiner virtual keyboard is ready. OpenEmu should receive these as hardware-level key events.', flush=True)

    def _wait_ready(self):
        deadline = time.time() + 15
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError('Karabiner bridge exited before becoming ready. Is the Karabiner daemon running?')
            line = self.proc.stdout.readline().strip()
            if line == 'READY':
                return
            if line.startswith(('CONNECT_FAILED','ERROR')):
                raise RuntimeError(f'Karabiner bridge failed: {line}')
        raise RuntimeError('Timed out waiting for Karabiner virtual keyboard. Run the setup script again.')

    def _usage(self, player, button):
        return PLAYER_MAPS.get(player, PLAYER_MAPS[1]).get(button)

    def _send(self, line):
        if self.proc.poll() is not None:
            raise RuntimeError('Karabiner bridge stopped')
        self.proc.stdin.write(line + '\n')
        self.proc.stdin.flush()
        reply = self.proc.stdout.readline().strip()
        if reply not in ('OK','READY'):
            raise RuntimeError(f'Karabiner bridge error: {reply or "no response"}')

    def button(self, player, button, pressed):
        usage = self._usage(player, button)
        if usage is None:
            return
        token = (player, button)
        if pressed and token not in self.held:
            self._send(f'DOWN {usage}')
            self.held.add(token)
        elif not pressed and token in self.held:
            self._send(f'UP {usage}')
            self.held.remove(token)

    def axis(self, player, axis, x, y):
        if axis != 'left':
            return
        self.button(player, 'LEFT', x < -0.45)
        self.button(player, 'RIGHT', x > 0.45)
        self.button(player, 'UP', y < -0.45)
        self.button(player, 'DOWN', y > 0.45)

    def release_all(self):
        if getattr(self, 'proc', None) and self.proc.poll() is None:
            try:
                self._send('CLEAR')
            except Exception:
                pass
        self.held.clear()

    def close(self):
        self.release_all()
        if getattr(self, 'proc', None) and self.proc.poll() is None:
            try:
                self.proc.stdin.write('QUIT\n')
                self.proc.stdin.flush()
                self.proc.wait(timeout=2)
            except Exception:
                self.proc.kill()
