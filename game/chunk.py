import pygame as pg

from .camera import Camera

from .block import Block


class Chunk:
    KEEP_ALIVE_TIME = 5

    def __init__(self, blocks, x, y, width, height):
        self.blocks = blocks

        size = (Block.WIDTH*width, Block.HEIGHT*height)

        self.surf = pg.Surface(size).convert_alpha()
        self.surf.fill(pg.Color(0, 0, 0, 0))

        self.x1 = x
        self.x2 = min(x+width, len(blocks[0]))

        self.y1 = y
        self.y2 = min(y+height, len(blocks))

        real_x = x * Block.WIDTH
        real_y = y * Block.HEIGHT

        real_width, real_height = size

        self.rect = pg.Rect(real_x,
                            real_y,
                            real_width,
                            real_height)

        self.alive_time = self.KEEP_ALIVE_TIME

        self.update()

    def update(self):
        self.surf.fill(pg.Color(0, 0, 0, 0))

        for y in range(self.y1, self.y2):
            for x in range(self.x1, self.x2):
                if self.blocks[y][x] is None:
                    continue

                local_x = (x-self.x1) * Block.WIDTH
                local_y = (y-self.y1) * Block.HEIGHT

                self.surf.blit(self.blocks[y][x].image.get(), (local_x, local_y))

    def deltimer(self, dtime):
        self.alive_time -= dtime

        return self.alive_time <= 0

    def draw(self, screen):
        info = pg.display.Info()
        offset_x, offset_y = Camera.get().get_position()
        draw_x = self.rect.x - offset_x
        draw_y = self.rect.y - offset_y
        if (-self.rect.width <= draw_x <= info.current_w + self.rect.width and
           -self.rect.height <= draw_y <= info.current_h + self.rect.height):
            screen.blit(self.surf, (draw_x, draw_y))

            self.alive_time = self.KEEP_ALIVE_TIME

            return 1
        return 0