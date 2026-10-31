"""Generate the app's document/Markdown icon in PNG and Windows ICO formats."""

from pathlib import Path

from PIL import Image, ImageDraw


BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / "assets"
OUTPUT.mkdir(exist_ok=True)

size = 1024
canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(canvas)

# Indigo tile and a high-contrast folded document read clearly at taskbar size.
draw.rounded_rectangle((30, 30, 994, 994), radius=220, fill="#4338CA")
draw.polygon([(675, 190), (818, 333), (818, 782), (720, 865), (253, 865), (205, 817), (205, 238), (253, 190)], fill="#FFFFFF")
draw.polygon([(675, 190), (675, 333), (818, 333)], fill="#C7D2FE")
draw.line([(675, 190), (675, 333), (818, 333)], fill="#A5B4FC", width=15, joint="curve")

# Markdown heading mark and two text lines.
ink = "#4338CA"
draw.line([(327, 425), (327, 595)], fill=ink, width=29)
draw.line([(414, 425), (414, 595)], fill=ink, width=29)
draw.line([(283, 477), (458, 477)], fill=ink, width=29)
draw.line([(283, 548), (458, 548)], fill=ink, width=29)
draw.rounded_rectangle((500, 460, 697, 490), radius=15, fill="#7C82D9")
draw.rounded_rectangle((500, 531, 648, 561), radius=15, fill="#7C82D9")

icon = canvas.resize((256, 256), Image.Resampling.LANCZOS)
icon.save(OUTPUT / "app.png")
canvas.save(OUTPUT / "app.ico", format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(f"Created {OUTPUT / 'app.png'} and {OUTPUT / 'app.ico'}")

