from math import atan2, degrees

from pygame.math import Vector2

from .entity import Entity


class Projectile(Entity):
    SPEED = 10
    
    TTL = 10
    
    SIZE = (8, 8)
    
    BRAKING = 1
    
    GRAVITY = 5
    
    TARGET_TAGS = []
    
    def __init__(self,
                 manager=None,
                 uuid=None,
                 position=(0, 0),
                 angle=0,
                 source_entity=None):
        super().__init__(
                 manager=manager,
                 uuid=uuid,
                 position=position,
                 velocity=Vector2(self.SPEED, 0).rotate(angle),
                 size=self.SIZE)
        
        self.lifetime = self.TTL
        self.source_entity = source_entity
    
    def update(self, dtime):
        super().update(dtime)
        
        self.angle = degrees(atan2(self.xv, self.yv)) - 90
        
        self.lifetime -= dtime
        
        if self.lifetime <= 0:
            self.manager.delentity(self.uuid)
            return
        
        for tag in self.TARGET_TAGS:
            for entity in self.manager.get_tagged_entities(tag):
                if entity is self.source_entity:
                    continue
                
                if entity.rect.colliderect(self.rect):
                    self.on_hit_entity(entity)
    
    def collide(self, by_x):
        self.world.is_collide(self, self._on_collide_x if by_x else self._on_collide_y)
        
    def on_hit_block(self, block):
        self.manager.delentity(self.uuid)
    
    def on_hit_entity(self, entity):
        pass
    
    def _on_collide_x(self, block, rect):
        """Collide callback for x"""
        if ((self.yv > 0 or block.collide_down)
            and (self.yv < 0 or block.collide_up)):
            
            if (self.xv > 0 and block.collide_right
                or (self.xv < 0 and block.collide_left)):
                self.on_hit_block(block)

    def _on_collide_y(self, block, rect):
        """Collide callback for y"""
        if ((self.yv > 0 and block.collide_up)
            or (self.yv < 0 and block.collide_down)):
            self.on_hit_block(block)
