import subprocess
from pathlib import Path
from .base import BaseDriver

HERE = Path(__file__).resolve().parent
SRC = HERE / 'macos_hid_helper.c'
BIN = HERE / 'retropad_macos_hid'

BUTTON_BITS = {
    'A':0, 'B':1, 'X':2, 'Y':3,
    'SQUARE':2, 'TRIANGLE':3, 'CROSS':0, 'CIRCLE':1,
    'L':4, 'L1':4, 'R':5, 'R1':5,
    'SELECT':6, 'COIN':6, 'START':7, 'MODE':6,
    'L2':8, 'R2':9, 'Z':10,
    'C_LEFT':11, 'C_UP':12, 'C_DOWN':13, 'C_RIGHT':14,
    '1':0, '2':1, '3':2, '4':3, '5':4, '6':5,
    'C':2,
}
DIRECTIONS = {'UP','DOWN','LEFT','RIGHT'}

class MacOSHIDDriver(BaseDriver):
    name='macOS virtual HID gamepad'
    def __init__(self):
        super().__init__()
        self._build_helper()
        self.proc=subprocess.Popen([str(BIN)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=None, text=True, bufsize=1)
        self.state={}
        self._ensure_player(1)

    def _build_helper(self):
        needs = (not BIN.exists()) or BIN.stat().st_mtime < SRC.stat().st_mtime
        if not needs: return
        cmd=['xcrun','clang','-O2','-Wall','-Wextra',str(SRC),'-framework','IOKit','-framework','CoreFoundation','-o',str(BIN)]
        try:
            subprocess.run(cmd, check=True)
        except FileNotFoundError as e:
            raise RuntimeError('Apple Command Line Tools are required. Run: xcode-select --install') from e
        except subprocess.CalledProcessError as e:
            raise RuntimeError('Could not compile the RetroPad macOS HID helper') from e

    def _ensure_player(self, p):
        if p not in self.state:
            self.state[p]={'buttons':0,'dirs':set(),'lx':0,'ly':0,'rx':0,'ry':0}
            reply=self._cmd(f'CREATE {p}')
            if not reply.startswith('READY'):
                raise RuntimeError(f'Could not create RetroPad P{p}: {reply}')
            self._send_neutral(p)
            print(f'RetroPad P{p} virtual HID ready', flush=True)
        return self.state[p]

    def _s(self,p):
        return self._ensure_player(p)

    def _send_neutral(self, p):
        self._cmd(f'REPORT {p} 00000800000000')

    def _cmd(self,line):
        if not self.proc or self.proc.poll() is not None: raise RuntimeError('macOS HID helper stopped')
        self.proc.stdin.write(line+'\n'); self.proc.stdin.flush()
        reply=self.proc.stdout.readline().strip()
        if reply.startswith('ERROR'):
            raise RuntimeError(f'HID helper error: {reply}. If compilation succeeded but device creation fails, macOS may be blocking virtual HID creation on this system.')
        return reply

    @staticmethod
    def _hat(d):
        u='UP' in d; dn='DOWN' in d; l='LEFT' in d; r='RIGHT' in d
        if u and r: return 1
        if r and dn: return 3
        if dn and l: return 5
        if l and u: return 7
        if u: return 0
        if r: return 2
        if dn: return 4
        if l: return 6
        return 8

    @staticmethod
    def _axis(v):
        v=max(-1.0,min(1.0,float(v)))
        n=int(round(v*127))
        return n & 0xff

    def _send(self,p):
        s=self._s(p); b=s['buttons']; hat=self._hat(s['dirs'])
        report=bytes([b&0xff,(b>>8)&0xff,hat,self._axis(s['lx']),self._axis(s['ly']),self._axis(s['rx']),self._axis(s['ry'])])
        self._cmd(f'REPORT {p} {report.hex()}')

    def set_profile(self, player, profile):
        super().set_profile(player, profile)
        self._s(player)

    def button(self, player, button, pressed):
        s=self._s(player)
        if button in DIRECTIONS:
            (s['dirs'].add if pressed else s['dirs'].discard)(button)
        else:
            bit=BUTTON_BITS.get(button)
            if bit is None: return
            if pressed: s['buttons'] |= (1<<bit)
            else: s['buttons'] &= ~(1<<bit)
        self._send(player)

    def axis(self, player, axis, x, y):
        s=self._s(player)
        if axis=='right': s['rx'],s['ry']=x,y
        else: s['lx'],s['ly']=x,y
        self._send(player)

    def release_all(self):
        for p,s in list(self.state.items()):
            s.update(buttons=0,lx=0,ly=0,rx=0,ry=0); s['dirs'].clear(); self._send(p)

    def close(self):
        try: self.release_all()
        except Exception: pass
        if getattr(self,'proc',None):
            try:
                self.proc.stdin.write('QUIT\n'); self.proc.stdin.flush(); self.proc.wait(timeout=1)
            except Exception: self.proc.kill()
