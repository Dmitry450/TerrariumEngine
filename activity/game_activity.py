import os

import pygame as pg

import game.texture as textures
import game.sound as sounds

from game.block import BlockDefHolder
from game.player import Player
from game.item_entity import ItemEntity
from game.camera import Camera
from game.world import World
from game.meta_manager import MetaManager
from game.entity_manager import EntityManager
from game.item import Item
from game.sound import getsound
from game.decorations import DecorationManager

from mods.manager import ModManager

from ui.label import Label
from ui.button import Button
from ui.inv_hotbar import InventoryHotbar
from ui.hotbar_selected import HotbarSelected
from ui.inventory_cell import InventoryCell

from utils.calls import Call

from worldfile.worldfile import decode, encode

from .activity import Activity, newactivity
from .default_parallax import DefaultParallax

import activity.main_menu_activity as mainmenu  # Cannot import MainMenuActivity because of cirlular import

from config import getcfg


config = getcfg()


class GameActivity(Activity):
    BG_COLOR = pg.Color(config["game.background"])
    
    BG_MUSIC = getsound(config["game.music"])  # TODO - play music based on biome
    
    INTERACT_DIST = config["player.interact_distance"]
    
    def __init__(self, path):
        super().__init__()
        
        modmanager = ModManager.get()
        
        modmanager.load_mods()
        
        textures.reload()  # Reload all textures from mods
        sounds.reload()  # Same with sounds

        BlockDefHolder.init_int_ids()             # Create int identifiers for
                                         # block definitions
        Player.register()
        ItemEntity.register()

        Camera.init()  # Create camera object
        
        self.parallax = DefaultParallax()
        
        self.decormanager = DecorationManager.new()

        self.background = pg.Surface(
            (self.app.WIN_WIDTH, self.app.WIN_HEIGHT))
        self.background.fill(self.BG_COLOR)
        
        savepath = os.path.join('saves', path)
        self.worldpath = os.path.join(savepath, 'world.tworld')
        self.metapath = os.path.join(savepath, 'world.meta')
        self.entitiespath = os.path.join(savepath, 'world.entities')
        
        file = open(self.worldpath, 'rb')
        
        decoded = decode(file.read())
        
        file.close()

        self.world = World.new(*decoded)
        
        modmanager.call_handlers('on_world_load', self.world)
        
        self.meta_manager = MetaManager.load(self.metapath)
        
        self.entity_manager = EntityManager.new()
        self.entity_manager.load(self.entitiespath)

        self.player = self.entity_manager.getentity('player')

        if self.player is None:
            self.player, _ = self.entity_manager.newentity('builtin:player', 'player')
        
        inv = self.player.get_inventory()
        
        modmanager.call_handlers('on_player_join', self.player)
        
        win_width, win_height = config["app.resolution"]
        
        ################################################################
        # Hotbar
        hotbar = InventoryHotbar(
            position=(20, 20),
            size=(510, 70))
            
        inv_width = inv.get_size('hotbar')
        inv_height = inv.get_size('main') // inv_width
        
        cell_size = 50
        space = 10

        for i in range(inv_width):
            x = (i+1)*space + cell_size*i + space
            InventoryCell(inv.get_item_ref('hotbar', i),
                          inv,
                          parent=hotbar,
                          position=(x, space),
                          size=(cell_size, cell_size))
        
        x = (self.player.selected_item+1)*space + cell_size*self.player.selected_item + space
        self.hotbar_selected = HotbarSelected(
                          parent=hotbar,
                          position=(x, space),
                          size=(cell_size, cell_size))
        
        self.overlay.add_element('hotbar', hotbar, True)
        
        ################################################################
        # Main inventory
        main_inventory = InventoryHotbar(
            position=(20, 140),
            size=(510, 280))

        for x in range(inv_width):
            for y in range(inv_height):
                InventoryCell(inv.get_item_ref('main', y*inv_width + x),
                              inv,
                              parent=main_inventory,
                              position=((x+1)*space + cell_size*x + space, 
                                        (y+1)*space + cell_size*y + space),
                              size=(cell_size, cell_size))

        self.overlay.add_element('inventory', main_inventory)
        
        ################################################################
        # Pause
        pause = Label(
            text="Paused",
            position=(win_width//2 - 250, win_height/2 - 220),
            size=(500, 400))
        
        Button(
            parent=pause,
            on_pressed=self.play,
            text="Continue",
            position=(100, 100),
            size=(300, 100))
        
        Button(
            parent=pause,
            on_pressed=Call(newactivity, mainmenu.MainMenuActivity),
            text="Quit",
            position=(100, 220),
            size=(300, 100))
        
        self.overlay.add_element('pause', pause)

        self.camera = Camera.get()
        self.camera.set_obj(self.player)
        self.camera.set_offset(self.app.WIN_WIDTH/2, self.app.WIN_HEIGHT/2)

        self.controls = {
            'left': False,
            'right': False,
            'up': False,
            'mouse': {
                'pressed': False,
                'press_time': 0,
            },
        }

        self.paused = False
        
        self.allow_event(pg.KEYUP)
        self.allow_event(pg.KEYDOWN)
        
        self._skipupdate = True
        # Loading blocks is too long process, so after is dtime becomes
        # a little bigger than often, so entities can teleport pass
        # blocks. This is temporary solution.
        # TODO - fix that problem by better way
    
    def open_inventory(self, inv, name, length):
        inv_width = length
        inv_height = inv.get_size(name) // length
        
        cell_size = 50
        space = 10
        
        inventory = InventoryHotbar(
            position=(20, 140),
            size=(510, 280))

        for x in range(inv_width):
            for y in range(inv_height):
                InventoryCell(inv.get_item_ref('main', y*inv_width + x),
                              inv,
                              parent=main_inventory,
                              position=((x+1)*space + cell_size*x + space, 
                                        (y+1)*space + cell_size*y + space),
                              size=(cell_size, cell_size))
        
        self.overlay.add_element('opened_inventory', inventory, True)
        self.overlay.show('inventory')
    
    def update_selected_item(self):
        inv_width = self.player.inventory.get_size('hotbar')
        inv_height = self.player.inventory.get_size('main') // inv_width
        
        cell_size = 50
        space = 10
        
        x = (self.player.selected_item+1)*space + cell_size*self.player.selected_item
        
        self.hotbar_selected.set_rect(
            position=(x+space, space),
            size=(cell_size, cell_size))
    
    def toggle_inventory_visibility(self):
        if self.overlay.is_visible('inventory'):
            self.overlay.hide('inventory')
            
            if self.overlay.get('opened_inventory') is not None:
                self.overlay.hide('opened_inventory')
        else:
            self.overlay.show('inventory')

    def update(self, dtime):
        if self._skipupdate:
            self._skipupdate = False
            return
            
        if not self.paused:
            if self.controls['mouse']['pressed']:
                istack = self.player.inventory.get_item('hotbar', self.player.selected_item)
                
                if not istack.empty():
                    x, y = pg.mouse.get_pos()
                    
                    cam_x, cam_y = self.camera.get_position()
                    
                    x += cam_x
                    y += cam_y
                    
                    if self.controls['mouse']['press_time'] == 0:
                        istack.item_t.on_press(self.player, istack, (x, y))
                        self.controls['mouse']['press_time'] += dtime
                    else:
                        istack.item_t.on_keep_press(
                            self.player,
                            istack,
                            (x, y), 
                            self.controls['mouse']['press_time'])
                        self.controls['mouse']['press_time'] += dtime

            self.player.update_presses(left=self.controls['left'],
                                       right=self.controls['right'],
                                       up=self.controls['up'])
            self.entity_manager.update(dtime)

            self.world.update(dtime)
            
            self.decormanager.update(dtime)

            self.camera.update_position()

    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        
        self.parallax.draw(screen)

        self.world.draw(screen)
        
        self.entity_manager.draw(screen)
        
        self.decormanager.draw(screen)

    def pause(self):
        self.overlay.show('pause')
        self.paused = True

    def play(self):
        self.overlay.hide('pause')
        self.paused = False
    
    def toggle_pause(self):
        if self.paused:
            self.play()
        else:
            self.pause()

    def on_event(self, event):
        if self.paused:
            super().on_event(event)
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_a:
                self.controls['left'] = True

            elif event.key == pg.K_d:
                self.controls['right'] = True

            elif event.key == pg.K_SPACE:
                self.controls['up'] = True
            
            elif event.key == pg.K_i:
                self.toggle_inventory_visibility()
            
            elif event.key == pg.K_e:
                self.interact()
            
            elif event.key == pg.K_ESCAPE:
                if self.overlay.is_visible('inventory'):
                    self.toggle_inventory_visibility()
                else:
                    self.toggle_pause()

        elif event.type == pg.KEYUP:
            if event.key == pg.K_a:
                self.controls['left'] = False

            elif event.key == pg.K_d:
                self.controls['right'] = False

            elif event.key == pg.K_SPACE:
                self.controls['up'] = False

        elif event.type == pg.MOUSEBUTTONDOWN and not self.overlay.is_visible('inventory'):
            if event.button == 1:
                self.controls['mouse']['pressed'] = True
            elif event.button in (4, 5):
                self.player.selected_item += 1 if event.button == 5 else -1
                
                if self.player.selected_item < 0:
                    self.player.selected_item = self.player.inventory.get_size('hotbar')-1
                elif self.player.selected_item >= self.player.inventory.get_size('hotbar'):
                    self.player.selected_item = 0
                
                self.update_selected_item()
        
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                self.controls['mouse']['pressed'] = False
                self.controls['mouse']['press_time'] = 0

        elif not (event.type == pg.MOUSEBUTTONUP and
                  not self.overlay.is_visible()):
            super().on_event(event)
    
    def interact(self):
        can_interact = []
        
        # Find all entities we can interact
        for entity in self.entity_manager.get_tagged_entities('interactive'):
            v = pg.math.Vector2(self.player.rect.center)
            
            if v.distance_to(entity.rect.center) <= self.INTERACT_DIST:
                can_interact.append(entity)
        
        if not can_interact:
            return  # No entities found
        
        # Cursor position in the world
        cursor = pg.math.Vector2(pg.mouse.get_pos()) + self.camera.get_position()
        
        # Nearest entity and distance to it. Initialize it with the first found entity
        nearest = (can_interact[0], cursor.distance_to(can_interact[0].rect.center))
        
        # Now find the nearest entity for the cursor
        for entity in can_interact[1:]:
            dist = cursor.distance_to(entity.rect.center)
            
            if dist < nearest[1]:
                nearest = (entity, dist)
        
        nearest[0].on_interact(self.player)
    
    def on_begin(self):
        self.app.music_player.play(self.BG_MUSIC)

    def on_end(self):
        print("Saving world...")
        
        try:
            self.app.music_player.stop()
        except pg.error:
            pass  # When closing game, pygame.mixer becomes not initialized

        blocksize = BlockDefHolder.registered_count()//255 + 1
        
        data = encode(self.world.world_data,
                      self.world.WORLD_WIDTH, self.world.WORLD_HEIGHT)
        
        self.meta_manager.save(self.metapath)
        self.entity_manager.save(self.entitiespath)

        file = open(self.worldpath, 'wb')

        file.write(data)

        file.close()
