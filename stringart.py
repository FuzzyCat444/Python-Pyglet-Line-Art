import pyglet
from pyglet import shapes
from pyglet import clock
from pyglet import image as img

import math
import random
import sys

arg_imagename = ''
arg_pegs = 300
arg_pixelcover = 25
if len(sys.argv) == 4:
    arg_imagename = sys.argv[1]
    arg_pegs = int(sys.argv[2])
    arg_pixelcover = float(sys.argv[3])
    
    print()
    print('{} {} {}'.format(arg_imagename, arg_pegs, arg_pixelcover))
else:
    print()
    print('Syntax: stringart.py <image path> <peg count> <pixel cover (0-100)>')
    print()
    print('A good value for <peg count> is 300.')
    print()
    print('<pixel cover> represents what percent of a whole pixel is removed ' +
          'when a line passes through it.')
    print('Should not be 0 or 100 exactly.') 
    print('A good value is 5.')
    exit()

class App:
    def __init__(self, width, height, batch):
        global arg_imagename
        global arg_pegs
        global arg_pixelcover
        
        size = min(width, height)
        r = size / 2
        
        self.stringring = StringRing(width / 2, height / 2, r, arg_pegs, 
            img.load(arg_imagename), arg_pixelcover, batch)
        
    def update(self, dt):
        self.stringring.update(dt)

class StringRing:
    def __init__(self, x, y, radius, pegcount, image, pixelcover, batch):
        self.x = x
        self.y = y
        self.radius = radius
        self.pegcount = pegcount
        self.image = image
        self.pixelcover = pixelcover / 100
        self.batch = batch
        self.width = min(self.image.width, self.image.height)
        self.size = self.width / 2
        rawdata = (self.image.get_image_data().
            get_data('rgb', 3 * self.image.width))
            
        self.pixelweights = []
        rawindex = 0
        for y in range(self.width):
            self.pixelweights.append([])
            i = rawindex
            for x in range(self.width):
                avg = (rawdata[i] + rawdata[i + 1] + rawdata[i + 2]) / (3 * 255)
                inv = 1 - avg
                self.pixelweights[y].append(inv)
                i += 3
            rawindex += 3 * self.image.width
                
        self.pegpos_img = []
        for i in range(self.pegcount):
            sz = self.size
            px, py = circlepoint(sz, sz, sz, i, self.pegcount)
            self.pegpos_img.append((math.floor(px), math.floor(py)))
        self.pegpos_irl = []
        for i in range(self.pegcount):
            self.pegpos_irl.append(circlepoint(self.x, self.y, self.radius, i, 
                self.pegcount))
            
        self.pegindex = random.randrange(self.pegcount)
        self.lastpegindex = self.pegindex
        self.pegpairs = set()
        self.timer = 0
        
        
        
        self.boardcircle = shapes.Circle(self.x, self.y, self.radius, 
            segments=100, color=(255, 255, 255), batch=batch)
            
        self.pegcircles = []
        for cx, cy in self.pegpos_irl:
            self.pegcircles.append(shapes.Circle(cx, cy, self.radius / 150, 
                segments=8, color=(0, 100, 0), batch=batch))
            
        self.stringlines = []
    
    def update(self, dt):
        self.timer += dt
        step = 1 / 20
        
        
        x1, y1 = self.pegpos_img[self.pegindex]
        
        index_a = random.randrange(self.pegcount)
        index_b = (index_a + self.pegcount // 3) % self.pegcount
        highest = 0
        highesti = randcircle(index_a, index_b, self.pegcount)
        for i in circlerange(index_a, index_b, self.pegcount):
            if i == self.pegindex:
                continue
            x2, y2 = self.pegpos_img[i]
            total = 0
            count = 0
            for bx, by in bresenham(x1, y1, x2, y2):
                if (bx < 0 or bx >= self.width or
                    by < 0 or by >= self.width):
                   continue
                total += self.pixelweights[by][bx]
                count += 1
            total /= count
            avg = total
            if avg > highest and not self.haspair(self.pegindex, i):
                highest = avg
                highesti = i
        
        x2, y2 = self.pegpos_img[highesti]
        for bx, by in bresenham(x1, y1, x2, y2):
            if (bx < 0 or bx >= self.width or
                by < 0 or by >= self.width):
               continue
            self.pixelweights[by][bx] -= self.pixelcover
        
        lx1, ly1 = self.pegpos_irl[self.pegindex]
        lx2, ly2 = self.pegpos_irl[highesti]
        self.stringlines.append(shapes.Line(lx1, ly1, lx2, ly2,
            color=(0, 0, 0), batch=self.batch))
        
        self.lastpegindex = self.pegindex
        self.pegindex = highesti
        self.insertpair(self.lastpegindex, self.pegindex)
            
        self.timer -= step
            
    def haspair(self, i, j):
        if j < i:
            i, j = j, i
        return (i, j) in self.pegpairs
        
    def insertpair(self, i, j):
        if j < i:
            i, j = j, i
        self.pegpairs.add((i, j))

def circlerange(i, j, n):
    if i < j:
        for x in range(i, j):
            yield x
    else:
        for x in range(i, n):
            yield x
        for x in range(j):
            yield x

def randcircle(i, j, n):
    if i < j:
        return random.randrange(i, j)
    else:
        a = j
        b = n - i
        c = random.randrange(a + b)
        if c < a:
            return random.randrange(j)
        else:
            return random.randrange(i, n)

def circlepoint(x, y, r, i, n):
    angle = 2 * math.pi * i / n
    return x + r * math.cos(angle), y + r * math.sin(angle)

def bresenham(x1, y1, x2, y2):
    diffx = x2 - x1
    diffy = y2 - y1
    if diffx == 0 and diffy == 0:
        return
    diffx += -1 if diffx < 0 else 1
    diffy += -1 if diffy < 0 else 1
    
    inc = 0
    length = 0
    axis = 0
    if abs(diffx) > abs(diffy):
        length = abs(diffx)
        inc = diffy / length
    else:
        length = abs(diffy)
        inc = diffx / length
        axis = 1
        
    x = x1
    y = y1
    err = 0
    for i in range(math.floor(length)):
        yield x, y
        if axis == 0:
            if diffx > 0:
                x += 1
            else:
                x -= 1
            err += inc
            if err >= 1:
                err -= 1
                y += 1
            elif err <= -1:
                err += 1
                y -= 1
        else:
            if diffy > 0:
                y += 1
            else:
                y -= 1
            err += inc
            if err >= 1:
                err -= 1
                x += 1
            elif err <= -1:
                err += 1
                x -= 1

def mainloop():
    width, height = 1000, 1000
    config = pyglet.gl.Config(sample_buffers=1, samples=4)
    window = pyglet.window.Window(width, height, 
        '{} {} {}'.format(arg_imagename, arg_pegs, arg_pixelcover), 
        vsync=False, config=config)
    batch = pyglet.graphics.Batch()
    app = App(width, height, batch)
        
    @window.event
    def on_draw():
        nonlocal window
        nonlocal batch
        window.clear()
        batch.draw()
        
    clock.schedule(app.update)
    
    pyglet.app.run()

if __name__ == '__main__':
    mainloop()