import traceback

import pygame as pg


class Sound:
    instances = {}
    
    def __init__(self, name, volume=1.0):
        self.name = name
        self.sound = None
        self.volume = volume
    
    def load(self, force=False):
        try:
            self.sound = pg.mixer.Sound(self.name)
            self.sound.set_volume(volume)
        except pg.error as e:
            print(f"Error: could not load sound {self.name}: {e}")
            self.sound = pg.mixer.Sound(b'')
        except FileNotFoundError as e:
            print(f'Error: could not load sound {self.name}: {e}')
            self.sound = pg.mixer.Sound(b'')

    def play(self, *args, **kwargs):
        if self.sound is not None:
            self.sound.play(*args, **kwargs)
        else:
            traceback.print_stack()
            print(f'Error: sound {self.name} is not loaded')


def getsound(name, volume=1.0):
    if Sound.instances.get(name):
        return Sound.instances[name]
    
    Sound.instances[name] = Sound(name, volume)
    
    return Sound.instances[name]


def load(force=False):
    for name in Sound.instances:
        Sound.instances[name].load(force)


def reload():
    load(True)
