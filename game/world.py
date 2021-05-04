import pygame as pg

from utils.coords import neighbours

import game.block as blockmod
from .chunk import Chunk
from .tick import Ticker

from .camera import Camera

from config import getcfg


config = getcfg()


class World:
    instance = None

    CHUNK_WIDTH = config["world.chunk_size"][0]
    CHUNK_HEIGHT = config["world.chunk_size"][1]

    def __init__(self, data, width, height):
        print("Initializing blocks...")

        self.WORLD_WIDTH = width
        self.WORLD_HEIGHT = height

        self.world_data = data

        self.chunks_x = self.WORLD_WIDTH//self.CHUNK_WIDTH + 1
        self.chunks_y = self.WORLD_HEIGHT//self.CHUNK_HEIGHT + 1

        self.chunks = [[None for x in range(self.chunks_x)] for y in range(self.chunks_y)]

        self.chunks_loaded = []

        self.camera = Camera.get()
        
        self.ticker = Ticker.new()
    
    def get_ticker(self):
        return self.ticker

    def is_collide(self, entity, on_collide):
        # block_w = 16, ent.rect.left = 128, ent.rect.right = 138, range = (8, 9)
        for x in self.worldrange_x(entity.rect.left, entity.rect.right):
            for y in self.worldrange_y(entity.rect.top, entity.rect.bottom):
                rect = pg.Rect(x*blockmod.Block.WIDTH, y*blockmod.Block.HEIGHT, blockmod.Block.WIDTH, blockmod.Block.HEIGHT)
                block = self.get_block(x, y, 0)
                if (block is not None and rect.colliderect(entity.rect)):
                    on_collide(block, rect)

    def worldrange_x(self, x1, x2):
        return range(max(0, x1//blockmod.Block.WIDTH), min(x2//blockmod.Block.WIDTH + 1, self.WORLD_WIDTH))

    def worldrange_y(self, y1, y2):
        return range(max(0, y1//blockmod.Block.HEIGHT), min(y2//blockmod.Block.HEIGHT + 1, self.WORLD_HEIGHT))

    def draw(self, screen):
        list(
            map(
                lambda chunk: chunk.draw(screen),
                self.chunks_loaded))

    def set_block(self, x, y, layer, id):
        if not self.within_bounds(x, y) or 0 > layer >= 3:
            return
        
        block_old = blockmod.BlockDefHolder.by_id(self._get_block_id(x, y, layer))
        block_new = blockmod.BlockDefHolder.by_id(id)
        
        if block_old is not None:
            block_old._on_destroy(x, y)

        self._set_block_id(x, y, layer, id)
        
        if block_new is not None:
            block_new.on_place(x, y)
        
        updated_chunks = []
        
        for nx, ny in neighbours(x, y):
            chunk_x, chunk_y = self.chunk_pos(nx*blockmod.Block.WIDTH, ny*blockmod.Block.HEIGHT)

            if (self.chunks[chunk_y][chunk_x] is not None
               and not self.chunks[chunk_y][chunk_x] in updated_chunks):
                self.chunks[chunk_y][chunk_x].update()
                updated_chunks.append(self.chunks[chunk_y][chunk_x])
            else:
                if not self.chunks[chunk_y][chunk_x] in updated_chunks:
                    self.load_chunk(chunk_x, chunk_y)

    def get_block(self, x, y, layer):
        if not self.within_bounds(x, y) or 0 > layer >= 3:
            return
        
        return blockmod.BlockDefHolder.by_id(self._get_block_id(x, y, layer))
    
    def set_fg_block(self, x, y, id):
        self.set_block(x, y, 0, id)

    def set_mg_block(self, x, y, id):
        self.set_block(x, y, 1, id)

    def set_bg_block(self, x, y, id):
        self.set_block(x, y, 2, id)

    def get_fg_block(self, x, y):
        return self.get_block(x, y, 0)

    def get_mg_block(self, x, y):
        return self.get_block(x, y, 1)

    def get_bg_block(self, x, y):
        return self.get_block(x, y, 2)

    def within_bounds(self, x, y):
        return 0 <= x < self.WORLD_WIDTH and 0 <= y < self.WORLD_HEIGHT
    
    def get_tiles(self, x, y):
        if not self.within_bounds(x, y):
            return ()
        else:
            result = ()
            
            bg = self.get_bg_block(x, y)
            mg = self.get_mg_block(x, y)
            fg = self.get_fg_block(x, y)
            
            if bg is not None:
                result += (bg,)
            if mg is not None:
                result += (mg,)
            if fg is not None:
                result += (fg,)
                
            return result

    def chunk_pos(self, x, y):
        x = int(x / blockmod.Block.WIDTH / self.CHUNK_WIDTH)
        y = int(y / blockmod.Block.HEIGHT / self.CHUNK_HEIGHT)

        return x, y

    def update(self, dtime):
        self.ticker.update(dtime)
        
        info = pg.display.Info()
        cam_x, cam_y = self.camera.get_position()

        left, top = self.chunk_pos(cam_x, cam_y)

        left -= 2
        top -= 2

        left, top = self.bound_chunk_position(left, top)

        right = left + int(info.current_w / blockmod.Block.WIDTH / self.CHUNK_WIDTH) + 4
        bottom = top + int(info.current_h / blockmod.Block.HEIGHT / self.CHUNK_HEIGHT) + 4

        right, bottom = self.bound_chunk_position(right, bottom)

        for y in range(top, bottom+1):
            for x in range(left, right+1):
                self.load_chunk(x, y)

        for chunk in self.chunks_loaded:
            if chunk.deltimer(dtime):
                self.del_chunk(*self.chunk_pos(chunk.rect.x, chunk.rect.y))

    def bound_chunk_position(self, x, y):
        x = max(0, min(self.chunks_x-1, x))
        y = max(0, min(self.chunks_y-1, y))

        return (x, y)

    def load_chunk(self, x, y):
        if self.chunks[y][x] is not None:
            return

        c = Chunk(self, 
                  x*self.CHUNK_WIDTH, y*self.CHUNK_HEIGHT,
                  self.CHUNK_WIDTH, self.CHUNK_HEIGHT)
        self.chunks[y][x] = c

        self.chunks_loaded.append(c)

    def del_chunk(self, x, y):
        c = self.chunks[y][x]

        if c is None:
            return

        self.chunks[y][x] = None

        self.chunks_loaded.remove(c)
    
    def _get_block_index(self, x, y, layer):
        '''Get index for array('I', <world>)'''
        return self.WORLD_WIDTH*y*3 + x*3 + layer
    
    def _get_block_id(self, x, y, layer):
        '''Get block identifier at given position and layer'''
        i = self._get_block_index(x, y, layer)
        
        return self.world_data[i]
    
    def _set_block_id(self, x, y, layer, id):
        '''Set block identifier at given position and layer'''
        i = self._get_block_index(x, y, layer)
        
        self.world_data[i] = id

    @classmethod
    def block_by_id(cls, id, x, y):
        """Initialize required block by id at given position"""
        return None if id == 0 else block.BlockDefHolder.by_id(id)

    @classmethod
    def id_from_block(cls, block):
        if block is None:
            return 0
        return block.ID

    @classmethod
    def get(cls):
        return cls.instance

    @classmethod
    def new(cls, data, width, height):
        cls.instance = cls(data, width, height)
        return cls.instance
