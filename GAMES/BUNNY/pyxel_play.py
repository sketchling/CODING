import pyxel
from pyxel_utils import Sprite



#my_sprite.add_sprite(0,0,2)


class App:
    my_sprite = Sprite(0,0,16,0,30,66)

    def __init__(self):
        self.CHARSPEED = 3
        self.posx = 31
        self.direction = 1
        pyxel.init(160, 120, title="Hello Pyxel")
        pyxel.image(0).load(0, 0, "assets/Bunny16x16v02.png")
        pyxel.run(self.update, self.draw)
        self.my_sprite.y = 66
        self.my_sprite.size = 16

        
    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        if pyxel.btn(pyxel.KEY_LEFT):
            self.posx -=self.CHARSPEED
            self.direction = 1
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.posx +=self.CHARSPEED
            self.direction = -1
        self.my_sprite.x = self.posx

        

    def draw(self):
        
        pyxel.cls(0)
        pyxel.text(55, 41, "Hello, Pyxel!" + str(self.posx), pyxel.frame_count % 16)
        #pyxel.blt(self.posx, 66, 0,0, 0, 16*self.direction, 16)
        self.my_sprite.draw_sprite()
        
       

App()