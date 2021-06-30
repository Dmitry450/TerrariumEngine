import json

import pygame as pg

from game.texture import gettexture, gettiled
from game.sound import getsound
from game.block import Block

import mods.manager as mods


def _tile(drawtype, path):
    if drawtype == 'image':
        return gettexture(mods.modpath(path))
    elif drawtype == 'tiled':
        return gettiled(mods.modpath(path), 8, 2)


def _inventory_image(path):
    if path is not None:
        return gettexture(mods.modpath(path))


def _hit_sound(path):
    if path is not None:
        return getsound(mods.modpath(path))


def _custom_rect(shape):
    if shape is not None:
        return pg.Rect(*shape)


def register_block(path):
    """Register block with parametres read from given file path.
    
    For parametres see game.block.Block
    """
    with open(path) as file:
        blockdef = json.load(file)
    
    class JSONBlock(Block):
        id = blockdef["id"]
        
        drawtype = blockdef.get("drawtype", Block.drawtype)
        
        layer = blockdef.get("layer", Block.layer)
        
        tilecomparable = blockdef.get("tilecomparable", Block.tilecomparable)
        
        tile = _tile(blockdef.get("drawtype", Block.drawtype), blockdef.get("image", ''))
        
        drops = blockdef.get("drops", [])
        
        replacable = blockdef.get("replacable", Block.replacable)
        
        level = blockdef.get("level", Block.level)
        
        tool_types = blockdef.get("tool_types", Block.tool_types)
        
        hits = blockdef.get("hits", Block.hits)
        
        hit_sound = _hit_sound(blockdef.get("hit_sound"))
        
        register_item = blockdef.get("register_item", Block.register_item)
        
        inventory_image = _inventory_image(blockdef.get("inventory_image", Block.inventory_image))
        
        collide_up = blockdef.get("collide_up", Block.collide_up)
        collide_down = blockdef.get("collide_down", Block.collide_down)
        collide_left = blockdef.get("collide_left", Block.collide_left)
        collide_right = blockdef.get("collide_right", Block.collide_right)
        
        custom_rect = _custom_rect(blockdef.get("custom_rect"))
    
    
    JSONBlock.register()
    
    return JSONBlock
