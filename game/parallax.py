from .game_object import GameObject
from .camera import Camera


class Parallax:
    
    def __init__(self, children=None):
        self.objects = []
        self.children = children or {}
        
    def draw(self, screen):
        for obj in self.objects:
            obj.update()
            obj.draw(screen)
        
        for child in self.children.values():
            child.draw(screen)
        
    def add_child(self, id, child):
        self.children[id] = child
    
    def get_child(self, id):
        return self.children.get(id)
    
    def get_child_recursive(self, ids, fullpath=None):
        if fullpath is None:
            fullpath = ids
        
        if len(ids) == 0:
            return
        elif len(ids) == 1:
            return self.get_child(ids[0])
        else:
            child = self.get_child(ids[0])
            
            if child is not None:
                return child.get_child_recursive(ids[1:], fullpath)
            
            print(f'Error: child not found: {ids[0]}, full path: {fullpath}')
    
    def add_object(self, obj, to_child=None):
        if to_child is None:
            self.objects.append(obj)
        else:
            if isinstance(to_child, str):
                child = self.get_child(to_child)
            else:
                child = self.get_child_recursive(to_child)
            
            if child is not None:
                child.add_object(obj)
    
    def del_object(self, obj, from_child=None):
        if from_child is None:
            try:
                self.objects.remove(obj)
            except ValueError:
                print('Error: Parallax.del_object(): object not found')
        else:
            if isinstance(to_child, str):
                child = self.get_child(to_child)
            else:
                child = self.get_child_recursive(to_child)
            
            if child is not None:
                child.del_object(obj)


class ParallaxElement(GameObject):
    texture = None
    size = None
    
    def __init__(self, parallax):
        super().__init__(0, 0, *self.size)
        
        self.image = self.texture
        self.parallax = parallax
    
    def get_position(self):
        return self.camera.get_position()
    
    def update(self):
        self.rect.x, self.rect.y = self.get_position()
