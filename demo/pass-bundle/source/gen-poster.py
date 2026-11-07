import json, math, random
from PIL import Image, ImageDraw

grid = json.load(open('/tmp/momo.json'))
ROWS, COLS = len(grid), len(grid[0])
PX = 40
W, H = 2048, 1024
OX = (W - COLS * PX) // 2
OY = (H - ROWS * PX) // 2

# Palettes keyed by the sprite's luminance chars.
GOLD = {  # normal hamster: warm golden fur, cream belly, pink ears and nose
    'O': (58, 38, 16), 'K': (26, 16, 6), 'H': (255, 255, 255),
    'B': (240, 168, 50), 'Y': (240, 168, 50), 'L': (255, 201, 94),
    'I': (242, 160, 168), 'S': (209, 138, 36), 'W': (255, 237, 190),
    'N': (239, 143, 150), 'P': (255, 227, 174), 'R': (185, 122, 30),
    'Z': (255, 246, 218),
}
STEEL = {  # terminator side: brushed steel, dark seams, glowing red eye
    'O': (10, 10, 12), 'K': (255, 32, 21), 'H': (255, 217, 208),
    'B': (154, 163, 171), 'Y': (154, 163, 171), 'L': (199, 206, 212),
    'I': (86, 94, 102), 'S': (107, 114, 120), 'W': (221, 227, 232),
    'N': (125, 133, 141), 'P': (167, 176, 184), 'R': (74, 80, 87),
    'Z': (232, 237, 241),
}

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

# Jagged torn-paper split line, smooth random walk.
random.seed(42)
jit, walk = [], 0
for y in range(H):
    walk += random.uniform(-1.6, 1.6)
    walk = max(-16, min(16, walk))
    jit.append(W // 2 + walk + 6 * math.sin(y / 110.0))

img = Image.new('RGB', (W, H))
px = img.load()
for y in range(H):
    t = y / H
    left_bg = lerp((126, 178, 172), (84, 138, 138), t)     # soft teal
    right_bg = lerp((158, 32, 20), (74, 10, 6), t)         # deep red
    sx = jit[y]
    for x in range(W):
        px[x, y] = left_bg if x < sx else right_bg

# Character, palette chosen per pixel by the split line.
for r, row in enumerate(grid):
    for c, ch in enumerate(row):
        if ch == '.':
            continue
        for dy in range(PX):
            y = OY + r * PX + dy
            if not (0 <= y < H):
                continue
            sx = jit[y]
            for dx in range(PX):
                x = OX + c * PX + dx
                if not (0 <= x < W):
                    continue
                pal = GOLD if x < sx else STEEL
                col = pal.get(ch)
                if col:
                    px[x, y] = col

# White torn edge over the split.
d = ImageDraw.Draw(img)
for y in range(H):
    sx = jit[y]
    d.line([(sx - 5, y), (sx + 5, y)], fill=(247, 243, 234))

img.save('/home/hatch/workspace/squeek-arena/design/headline-poster.png')

# LED dot simulation, like the form's conversion: dots on black.
DW, DH = 160, 80
dots = Image.new('RGB', (W, H), (8, 8, 10))
dd = ImageDraw.Draw(dots)
cell_w, cell_h = W / DW, H / DH
small = img.resize((DW, DH), Image.LANCZOS)
sp = small.load()
for j in range(DH):
    for i in range(DW):
        col = sp[i, j]
        if sum(col) < 40:
            continue
        cx, cy = (i + 0.5) * cell_w, (j + 0.5) * cell_h
        r = cell_w * 0.36
        dd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
dots.save('/home/hatch/workspace/squeek-arena/design/headline-poster-led.png')
print('saved poster + led simulation')
