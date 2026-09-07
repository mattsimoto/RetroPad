from .base import BaseDriver
try: import vgamepad as vg
except ImportError as ex: raise RuntimeError('vgamepad is required: pip install vgamepad') from ex
B={
 'A':vg.XUSB_BUTTON.XUSB_GAMEPAD_A,'B':vg.XUSB_BUTTON.XUSB_GAMEPAD_B,'X':vg.XUSB_BUTTON.XUSB_GAMEPAD_X,'Y':vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
 'CROSS':vg.XUSB_BUTTON.XUSB_GAMEPAD_A,'CIRCLE':vg.XUSB_BUTTON.XUSB_GAMEPAD_B,'SQUARE':vg.XUSB_BUTTON.XUSB_GAMEPAD_X,'TRIANGLE':vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
 'UP':vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,'DOWN':vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,'LEFT':vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,'RIGHT':vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
 'L':vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,'R':vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,'L1':vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,'R1':vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
 'START':vg.XUSB_BUTTON.XUSB_GAMEPAD_START,'SELECT':vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK
}
class WindowsVGamepadDriver(BaseDriver):
    name='Windows virtual Xbox 360 gamepad'
    def __init__(self):super().__init__();self.pads={}
    def _pad(self,p):
        if p not in self.pads:self.pads[p]=vg.VX360Gamepad()
        return self.pads[p]
    def button(self,p,b,pressed):
        pad=self._pad(p)
        if b=='L2':pad.left_trigger(value=255 if pressed else 0);pad.update();return
        if b=='R2':pad.right_trigger(value=255 if pressed else 0);pad.update();return
        code=B.get(b)
        if code:(pad.press_button if pressed else pad.release_button)(button=code);pad.update()
    def axis(self,p,axis,x,y):
        pad=self._pad(p);y=-y
        if axis=='left':pad.left_joystick_float(x_value_float=x,y_value_float=y)
        else:pad.right_joystick_float(x_value_float=x,y_value_float=y)
        pad.update()
    def release_all(self):
        for pad in self.pads.values():pad.reset();pad.update()
