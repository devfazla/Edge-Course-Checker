"""Generate the Edge Course Checker logo (PNG + ICO) in the app palette."""
import os, math
from PIL import Image, ImageDraw, ImageFont

SS = 4          # supersampling factor for smooth edges
S = 1024        # final size
H = S * SS

BG    = "#eef1f4"
TEAL  = "#0f766e"
DARK  = "#115e59"

img = Image.new("RGB", (H, H), BG)
d = ImageDraw.Draw(img)

cx, cy = H // 2, H // 2
R = int(0.40 * H)                       # hexagon radius (pointy top/bottom)
SW = int(0.05 * H)                      # outline stroke width

def pt(x, y):
    return (int(x), int(y))

# ---- hexagon badge outline ----
hexpts = []
for k in range(6):
    ang = math.pi / 2 + k * math.pi / 3
    hexpts.append(pt(cx + R * math.cos(ang), cy - R * math.sin(ang)))
d.polygon(hexpts, fill=BG, outline=TEAL, width=SW)
for p in hexpts:                        # rounded corner joins
    r = SW // 2
    d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], outline=TEAL, width=SW)

# ---- bold lowercase 'e' centered in the badge ----
def load_font(size):
    candidates = [
        r"C:\Windows\Fonts\seguisbi.ttf",   # Segoe UI Italic (a stylish 'e')
        r"C:\Windows\Fonts\seguisb.ttf",    # Segoe UI Semibold
        r"C:\Windows\Fonts\calibrib.ttf",   # Calibri Bold
        r"C:\Windows\Fonts\arialbd.ttf",    # Arial Bold
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()

TXT = "e"
font = load_font(int(0.92 * H))
bbox = d.textbbox((0, 0), TXT, font=font)
gw = bbox[2] - bbox[0]
gh = bbox[3] - bbox[1]
d.text((cx - gw / 2 - bbox[0], cy - gh / 2 - bbox[1]), TXT, fill=DARK, font=font)

# ---- downscale (antialiased) ----
final = img.resize((S, S), Image.LANCZOS)

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(out_dir, exist_ok=True)
final.save(os.path.join(out_dir, "logo.png"))
final.resize((256, 256), Image.LANCZOS).save(os.path.join(out_dir, "logo_256.png"))

ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
final.save(os.path.join(out_dir, "icon.ico"), sizes=ico_sizes)

print("saved:", out_dir)
