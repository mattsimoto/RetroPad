from .base import BaseDriver
try:
    from evdev import UInput, ecodes as e, AbsInfo
except ImportError as ex:
    raise RuntimeError('python-evdev is required: pip install evdev') from ex

BUTTON={
 'A':e.BTN_SOUTH,'B':e.BTN_EAST,'X':e.BTN_NORTH,'Y':e.BTN_WEST,
 'C':e.BTN_C,'Z':e.BTN_Z,'C_UP':e.BTN_TRIGGER_HAPPY1,'C_DOWN':e.BTN_TRIGGER_HAPPY2,'C_LEFT':e.BTN_TRIGGER_HAPPY3,'C_RIGHT':e.BTN_TRIGGER_HAPPY4,
 'CROSS':e.BTN_SOUTH,'CIRCLE':e.BTN_EAST,'SQUARE':e.BTN_WEST,'TRIANGLE':e.BTN_NORTH,
 'L':e.BTN_TL,'R':e.BTN_TR,'L1':e.BTN_TL,'R1':e.BTN_TR,'L2':e.BTN_TL2,'R2':e.BTN_TR2,
 'START':e.BTN_START,'SELECT':e.BTN_SELECT,'MODE':e.BTN_MODE,'COIN':e.BTN_SELECT,
 '1':e.BTN_SOUTH,'2':e.BTN_EAST,'3':e.BTN_NORTH,'4':e.BTN_WEST,'5':e.BTN_TL,'6':e.BTN_TR
}
class LinuxUInputDriver(BaseDriver):
    name='Linux uinput virtual gamepad'
    def __init__(self):
        super().__init__(); self.pads={}; self.states={}
    def _pad(self,p):
        if p in self.pads:return self.pads[p]
        caps={
          e.EV_KEY:list(set(BUTTON.values())),
          e.EV_ABS:[
            (e.ABS_X,AbsInfo(0,-32768,32767,16,128,0)),(e.ABS_Y,AbsInfo(0,-32768,32767,16,128,0)),
            (e.ABS_RX,AbsInfo(0,-32768,32767,16,128,0)),(e.ABS_RY,AbsInfo(0,-32768,32767,16,128,0)),
            (e.ABS_HAT0X,AbsInfo(0,-1,1,0,0,0)),(e.ABS_HAT0Y,AbsInfo(0,-1,1,0,0,0))]
        }
        self.pads[p]=UInput(caps,name=f'RetroPad P{p}',version=0x2);return self.pads[p]
    def button(self,p,b,pressed):
        pad=self._pad(p)
        if b in ('LEFT','RIGHT','UP','DOWN'):
            st=self.states.setdefault(p,{'LEFT':0,'RIGHT':0,'UP':0,'DOWN':0});st[b]=1 if pressed else 0
            pad.write(e.EV_ABS,e.ABS_HAT0X,st['RIGHT']-st['LEFT']);pad.write(e.EV_ABS,e.ABS_HAT0Y,st['DOWN']-st['UP']);pad.syn();return
        code=BUTTON.get(b)
        if code is not None:pad.write(e.EV_KEY,code,1 if pressed else 0);pad.syn()
    def axis(self,p,axis,x,y):
        pad=self._pad(p);ax,ay=(e.ABS_X,e.ABS_Y) if axis=='left' else (e.ABS_RX,e.ABS_RY)
        pad.write(e.EV_ABS,ax,int(max(-1,min(1,x))*32767));pad.write(e.EV_ABS,ay,int(max(-1,min(1,y))*32767));pad.syn()
    def release_all(self):
        for pad in self.pads.values():
            for code in set(BUTTON.values()):
                try:pad.write(e.EV_KEY,code,0)
                except:pass
            try:pad.syn()
            except:pass
    def close(self):
        self.release_all()
        for pad in self.pads.values():
            try:pad.close()
            except:pass
