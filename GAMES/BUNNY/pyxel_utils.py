from turtle import st
import pyxel

class Vect2D:
  '''Simple 2D coordinate object'''
  def __init__(self,x:int,y:int):
    self.vect2d = (x,y)
    self.x = x
    self.y = y
    
class Rect:
  '''Rectangle class for simpler collision detection'''  
  #method to set rectangle bounds
  def set_rect(self,x:int,y:int,width:int,height:int):
    self.x = x
    self.y = y
    self.width = width
    self.height = height
    self.top_left = Vect2D(x,y)
    self.top_right = Vect2D(x+ width,y)
    self.bottom_left = Vect2D(x,y+height)
    self.bottom_right = Vect2D(x+width,y+height)
  
  def __init__(self,x,y,width,height):
    self.set_rect(x,y,width,height)


class Sprite:
    '''Initialise a sprite with: 
    U,V on image sheet
    x pixel size (assume square)
    which sprite sheet 0-2 
    '''
    #Collision rect is always parented to sprite coordinates 

    def __init__(self,u,v,xsize,sprite_sheet:int = 0) -> None : 
        
        self.size = xsize
        self.direction_toggle_x : int = 1
        self.direction_toggle_y : int = 1
        self.sprite_sheet : int = sprite_sheet
        #add the pointer for the first image
        self.frames : list = []
        self.frames.append((u,v,Rect(0,0,xsize,xsize)))
        self.current_frame = 0
        #optional args to preload a starting position

        self.x :int =0
        self.y :int =0
          
        self.alpha_color = 0
    
    #might be simpler to add by slot not pixel coords - maybe second version _uv
    def add_frames(self,u:int,v:int,num_frames:int):
      #adds pointers to frames - keeps going across horizontally by numframes* sprite size
      #adds default collision rect for each frame
      for i in range(num_frames):
        self.frames.append((u+((i+1)* self.size),v,Rect(0,0,self.size,self.size)))
  
    
    def colliding_with_sprite(self,target):
      if ((target.frames[current_frame][2].top_left.x < self.frames[current_frame][2].top_left.x < target.frames[current_frame][2].top_right.x) and 
      (target.frames[current_frame][2].top_left.y < self.frames[current_frame][2].top_left.y < target.frames[current_frame][2].bottom_left.y)) or ((target.frames[current_frame][2].top_left.x < self.frames[current_frame][2].bottom_right.x < target.frames[current_frame][2].top_right.x) and 
      (target.frames[current_frame][2].top_left.y < self.frames[current_frame][2].bottom_right.y < target.frames[current_frame][2].bottom_left.y)) :
        return True
      else:
        return False  

class Actor:
  def __init__(self,name,sprite : Sprite,starting_x :int,starting_y:int):
    '''
    Actor is a base class for anything that moves in the game. the Player, Enemies etc
    Each Actor has:
    Sprite
    XY pos
    Speed
    gravity
    '''

    self.sprite = sprite
    self.name = name
    self.velocity = Vect2D(0,0)
    self.pos = Vect2D(starting_x,starting_y)
    self.gravity = 0
    self.direction = 1
  
  def draw_sprite(self):  
      for frame in self.sprite.frames:
        #print(f'{self.x}, {self.y}, {self.sprite_sheet},{frame[0]},{frame[1]*self.direction}, {self.size}, {self.size}, {self.alpha_color}')
        pyxel.blt(self.pos.x, self.pos.y, self.sprite.sprite_sheet,self.sprite.frames[self.sprite.current_frame][0],self.sprite.frames[self.sprite.current_frame][1]* self.direction_toggle_x,self.sprite.size,self.sprite.size, self.sprite.alpha_color)
        
  def is_colliding_with_tile(self,tile_list):
    'checks against collisions with all tile tuples in the tilelist'
    pass
  
  def is_colliding_with_actor(self,target_actor):
    pass
      
