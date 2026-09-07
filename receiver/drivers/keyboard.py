from .base import BaseDriver
try:
    from pynput.keyboard import Controller, Key
except ImportError as e:
    raise RuntimeError('pynput is required for keyboard fallback') from e

MAP={
 'UP':Key.up,'DOWN':Key.down,'LEFT':Key.left,'RIGHT':Key.right,
 'A':'x','B':'z','X':'s','Y':'a','C':'c','Z':'d',
 'C_UP':'i','C_DOWN':'k','C_LEFT':'j','C_RIGHT':'l',
 'CROSS':'x','CIRCLE':'z','SQUARE':'a','TRIANGLE':'s',
 'L':'q','R':'w','L1':'q','R1':'w','L2':'e','R2':'r',
 'START':Key.enter,'SELECT':Key.shift,'MODE':Key.tab,'COIN':'5',
 '1':'z','2':'x','3':'c','4':'a','5':'s','6':'d'
}
class KeyboardDriver(BaseDriver):
    name='keyboard fallback'
    def __init__(self): super().__init__(); self.k=Controller(); self.held=set(); self.axis_held={}
    def button(self,player,button,pressed):
        key=MAP.get(button)
        if key is None:return
        token=(player,str(key))
        if pressed and token not in self.held:self.k.press(key);self.held.add(token)
        elif not pressed and token in self.held:self.k.release(key);self.held.remove(token)
    def axis(self,player,axis,x,y):
        if axis!='left': return
        for name,on in [('LEFT',x<-.45),('RIGHT',x>.45),('UP',y<-.45),('DOWN',y>.45)]: self.button(player,name,on)
    def release_all(self):
        for _,keystr in list(self.held):
            for key in MAP.values():
                if str(key)==keystr:
                    try:self.k.release(key)
                    except:pass
        self.held.clear()
