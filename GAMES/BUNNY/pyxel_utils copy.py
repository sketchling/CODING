import pyxel

class Sprite:
    #Initialise a sprite with a pixel size - use this to calculate position in sprite bank
    #add frames to it from the image bank. - Sprite stores current frame. Frames
    #are a list of tuples with the uv and size of the sprite
    size:int
    direction : int 
    sprite_sheet : int
    sprite : list
    frame : int
    size : int 
    x : int 
    y : int 
    alpha_color : int

    def __init__(self,xsize,*args) -> None : #*args in case I need to specify non-square sprites later
        self.size = xsize
        self.direction : int = 0
        self.sprite_sheet : int = 0
        self.sprite : list = [(0,0)]
        self.frame = 0
        self.size : int = 16
        self.x : int = 0
        self.y : int = 0
        self.alpha_color = 0

    '''def add_sprite(self,u :int,v : int,num_across: int = 1) -> None :
        
        for i in range(num_across):
            self.sprite.append((u+ (num_across-1)*self.size,v))
    '''        
    def draw_sprite(self): 
        pyxel.blt(self.x, self.y, self.sprite_sheet,self.sprite[self.frame][0],self.sprite[self.frame][1]*self.direction, self.alpha_color)
