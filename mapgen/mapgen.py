import multiprocessing as mp

from game.block import Block

from worldfile.worldfile import encode


class Mapgen(mp.Process):
    """Base mapgen class"""

    def __init__(self, mods, output, width, height, status_v, done_v):
        super().__init__()

        Block.sort_registered_entries()

        self.mods = mods

        self.ofile = open(output, 'wb')

        self.width = width
        self.height = height

        self.foreground = [[0 for i in range(self.width)] for i in range(self.height)]
        self.midground = [[0 for i in range(self.width)] for i in range(self.height)]
        self.background = [[0 for i in range(self.width)] for i in range(self.height)]
        
        self.status = status_v  # String status of a mapgen
        self.done = done_v  # How much work done (in percent)

    def save(self):
        blocksize = int(Block.registered_count()/256) + 1
        data = encode(
            self.foreground,
            self.midground,
            self.background,
            blocksize)
        self.ofile.write(data)
        self.ofile.close()
        
        self.set_status(done=-1)
    
    def put_foreground(self, x, y, blockid):
        self.foreground[y][x] = blockid

    def put_midground(self, x, y, blockid):
        self.midground[y][x] = blockid

    def put_background(self, x, y, blockid):
        self.background[y][x] = blockid
    
    def get_foreground(self, x, y):
        return self.foreground[y][x]
    
    def get_midground(self, x, y):
        return self.midground[y][x]
    
    def get_background(self, x, y):
        return self.background[y][x]
    
    def set_status(self, string=None, done=None):
        if string is not None:
            with self.status.get_lock():
                self.status.value = string
        
        if done is not None:
            with self.done.get_lock():
                self.done.value = done

    def run(self):
        self.set_status(string=f"Started mapgen process with pid {self.pid}")
