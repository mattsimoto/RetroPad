class BaseDriver:
    name='base'
    def __init__(self): self.profiles={}
    def set_profile(self, player, profile): self.profiles[player]=profile
    def button(self, player, button, pressed): raise NotImplementedError
    def axis(self, player, axis, x, y): pass
    def release_all(self): pass
    def close(self): self.release_all()
