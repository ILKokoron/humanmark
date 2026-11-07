import json, math, random
from PIL import Image, ImageDraw, ImageFilter

grid = [list(r) for r in json.load(open('/tmp/momo.json'))]
# Two extra rows on top for the robot antenna.
grid = [list('.' * 26), list('.' * 26)] + grid
grid[0][19] = 'K'   # antenna tip (red on the steel side)
grid[1][19] = 'O'   # antenna stem
grid[2][19] = 'O'   # stem continues to the ear (row 2 was the empty top row)
# Robot plate seams + rivets (right half cells).
for c in range(16, 22):
    if grid[8][c] == 'B':
        grid[8][c] = 'S'
for (r, c) in [(9, 16), (9, 21)]:
    if grid[r][c] == 'B':
        grid[r][c] = 'O'
for r in range(15, 20):
    if grid[r][21] == 'B':
        grid[r][21] = 'S'
# Blush on the normal side's cheek.
for (r, c) in [(15, 6), (16, 6)]:
    if grid[r][c] == 'B':
        grid[r][c] = 'N'
grid = [''.join(r) for r in grid]

ROWS, COLS = len(grid), len(grid[0])
PX = 38
W, H = 2048, 1024
OX = (W - COLS * PX) // 2
OY = (H - ROWS * PX) // 2

GOLD = {  # brighter and warmer than v1
    'O': (56, 36, 14), 'K': (24, 14, 4), 'H': (255, 255, 255),
    'B': (255, 178, 44), 'Y': (255, 178, 44), 'L': (255, 209, 102),
    'I': (246, 150, 160), 'S': (224, 146, 34), 'W': (255, 240, 196),
    'N': (244, 128, 140), 'P': (255, 230, 176), 'R': (198, 130, 28),
    'Z': (255, 248, 224),
}
STEEL = {  # darker, harder machine greys; red eye
    'O': (6, 6, 8), 'K': (255, 26, 16), 'H': (255, 220, 210),
    'B': (126, 136, 145), 'Y': (126, 136, 145), 'L': (178, 186, 194),
    'I': (58, 64, 72), 'S': (78, 85, 93), 'W': (205, 212, 219),
    'N': (100, 108, 116), 'P': (148, 157, 166), 'R': (48, 53, 60),
    'Z': (216, 222, 228),
}

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

random.seed(7)
jit, walk = [], 0
wid, wwalk = [], 11.0
for y in range(H):
    walk += random.uniform(-2.4, 2.4)
    walk = max(-20, min(20, walk))
    wwalk += random.uniform(-0.7, 0.7)
    wwalk = max(8.0, min(15.0, wwalk))
    jit.append(W // 2 + walk + 5 * math.sin(y / 90.0))
    wid.append(wwalk)

img = Image.new('RGB', (W, H))
px = img.load()
for y in range(H):
    t = y / H
    left_bg = lerp((156, 208, 198), (112, 178, 170), t)   # brighter teal
    right_bg = lerp((104, 16, 9), (26, 4, 3), t)          # much darker red
    sx = jit[y]
    for x in range(W):
        px[x, y] = left_bg if x < sx else right_bg

d = ImageDraw.Draw(img)
# Faint circuit traces on the robot side's background.
for (x0, y0, x1, y1) in [(1560, 180, 1900, 180), (1900, 180, 1900, 420),
                          (1500, 760, 1820, 760), (1820, 760, 1820, 560),
                          (1620, 90, 1620, 300)]:
    d.line([(x0, y0), (x1, y1)], fill=(64, 12, 8), width=5)
    d.ellipse([x1 - 9, y1 - 9, x1 + 9, y1 + 9], outline=(88, 18, 12), width=4)
# Soft warm glow behind the normal hamster.
glow = Image.new('RGB', (W, H), (0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([OX - 120, 60, W // 2 + 190, H - 40], fill=(46, 34, 10))
img = Image.blend(img, Image.composite(Image.new('RGB', (W, H), (255, 226, 150)), img, glow.convert('L').filter(ImageFilter.GaussianBlur(60))), 0.25)
px = img.load()

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

# Red glow around the robot eye (eye cluster sits around cols 15-18, rows 11-13 in the padded grid).
eye = Image.new('RGB', (W, H), (0, 0, 0))
ed = ImageDraw.Draw(eye)
ex, ey = OX + 16.5 * PX, OY + 12 * PX
ed.ellipse([ex - 95, ey - 95, ex + 95, ey + 95], fill=(120, 8, 4))
eye = eye.filter(ImageFilter.GaussianBlur(45))
img = Image.fromarray((__import__('numpy').asarray(img, dtype='int16') + __import__('numpy').asarray(eye, dtype='int16')).clip(0, 255).astype('uint8')) if False else img
# (numpy-free glow: simple additive via point ops fallback)
from PIL import ImageChops
img = ImageChops.add(img, eye, 1, 0)

# The energy crack divider: layered bands, white-hot core.
seam = Image.new('RGB', (W, H), (0, 0, 0))
sd = ImageDraw.Draw(seam)
for y in range(H):
    sx, hw = jit[y], wid[y]
    for dx in range(-int(hw * 2.4), int(hw * 2.4) + 1):
        a = abs(dx)
        if a <= hw * 0.55:
            col = (255, 252, 244)
        elif a <= hw * 1.05:
            col = (255, 176, 66) if dx > 0 else (120, 110, 255)
        elif a <= hw * 1.6:
            col = (255, 64, 30) if dx > 0 else (64, 170, 255)
        else:
            col = (90, 14, 8) if dx > 0 else (16, 52, 92)
        x = int(sx + dx)
        if 0 <= x < W:
            sd.point((x, y), fill=col)
glow_seam = seam.filter(ImageFilter.GaussianBlur(16))
img = ImageChops.add(img, ImageChops.multiply(glow_seam, Image.new('RGB', (W, H), (90, 90, 90))), 1, 0)
img = ImageChops.add(img, seam, 1, 0)
img.save('/home/hatch/workspace/squeek-arena/design/headline-poster-v2.png')

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
dots.save('/home/hatch/workspace/squeek-arena/design/headline-poster-v2-led.png')
print('saved v2 poster + led')
