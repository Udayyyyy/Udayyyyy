"""Generate the profile's static SVG and subtle GIF headers. Requires Pillow.

Set HEADER_BOLD_FONT and HEADER_MONO_FONT to use other installed fonts.
All artwork is drawn from the same vector primitives; text remains stationary.
"""

from pathlib import Path
from html import escape
import math
import os

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
BACKGROUND = "#0D1117"
INK = "#F0F3F6"
MUTED = "#8B949E"
RULE = "#39424D"
ACCENT = "#F39073"
HALO = "#3F2D2B"
TRAIL = "#925A49"
TRAIL_FAINT = "#493731"
SCALE = 2


def font_path(variable, candidates):
    options = [os.environ.get(variable, ""), *candidates]
    return next(str(Path(p)) for p in options if p and Path(p).is_file())


BOLD = font_path("HEADER_BOLD_FONT", [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
])
MONO = font_path("HEADER_MONO_FONT", [
    "/System/Library/Fonts/Menlo.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
])


def layout(mobile=False):
    if mobile:
        return {
            "size": (560, 230), "axis": (32, 528, 195),
            "texts": [
                (32, 40, "APPLIED AI / EVALUATION", 16, MUTED, "mono", 0),
                (27, 118, "Uday Radadiya", 58, INK, "bold", -2.2),
                (32, 157, "BENCHMARKS / RL / VERIFIERS", 17, MUTED, "mono", 0),
            ],
            "labels": [],
        }
    return {
        "size": (1120, 244), "axis": (704, 1056, 122),
        "texts": [
            (34, 48, "APPLIED AI / EVALUATION", 16, MUTED, "mono", 0),
            (28, 132, "Uday Radadiya", 74, INK, "bold", -3.0),
            (34, 188, "BENCHMARKS / ENVIRONMENTS / VERIFIERS", 17, MUTED, "mono", 0),
        ],
        "labels": [(704, "task"), (880, "agent"), (1056, "check")],
    }


def fade(color, opacity):
    foreground = bytes.fromhex(color[1:])
    background = bytes.fromhex(BACKGROUND[1:])
    return "#" + "".join(f"{round(a * opacity + b * (1-opacity)):02x}"
                         for a, b in zip(foreground, background))


def primitives(spec, progress, opacity=1):
    width, height = spec["size"]
    start, end, y = spec["axis"]
    shapes = [("rect", (0, 0, width, height, 6, BACKGROUND))]
    shapes += [("text", item) for item in spec["texts"]]
    shapes += [("text_center", (x, 86, label, 17, MUTED, "mono", 0))
               for x, label in spec["labels"]]
    shapes.append(("line", (start, y, end, y, RULE, 1.6)))
    for x in [start, (start + end) / 2, end]:
        shapes.append(("circle", (x, y, 4.5, BACKGROUND, MUTED, 1.4)))
    x = start + (end - start) * progress
    if opacity > 0:
        for length, color in [(44, TRAIL_FAINT), (25, TRAIL)]:
            shapes.append(("line", (max(start, x-length), y, x, y, fade(color, opacity), 3.2)))
        shapes.append(("circle", (x, y, 12, fade(HALO, opacity), None, 0)))
        shapes.append(("circle", (x, y, 6.2, fade(ACCENT, opacity), None, 0)))
    return shapes


def svg(spec, progress=1):
    width, height = spec["size"]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<title>Uday Radadiya — Applied AI and evaluation</title>',
           '<desc>Benchmarks, RL environments, and verifiers. A signal passes from a task through an agent to a check.</desc>']
    for kind, values in primitives(spec, progress):
        if kind == "rect":
            x, y, w, h, r, fill = values
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"/>')
        elif kind in ("text", "text_center"):
            x, y, content, size, fill, face, tracking = values
            family = "Arial, Helvetica, sans-serif" if face == "bold" else "Menlo, Consolas, monospace"
            weight = "700" if face == "bold" else "400"
            anchor = "middle" if kind == "text_center" else "start"
            out.append(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" letter-spacing="{tracking}" text-anchor="{anchor}" fill="{fill}">{escape(content)}</text>')
        elif kind == "line":
            x1, y1, x2, y2, color, stroke = values
            out.append(f'<path d="M{x1} {y1}H{x2}" fill="none" stroke="{color}" stroke-width="{stroke}"/>')
        elif kind == "circle":
            x, y, r, fill, stroke, stroke_width = values
            border = f' stroke="{stroke}" stroke-width="{stroke_width}"' if stroke else ""
            out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"{border}/>')
    out.append('</svg>')
    return "\n".join(out) + "\n"


def raster(spec, progress, opacity=1):
    width, height = spec["size"]
    image = Image.new("RGB", (width * SCALE, height * SCALE), BACKGROUND)
    draw = ImageDraw.Draw(image)
    for kind, values in primitives(spec, progress, opacity):
        if kind == "rect":
            x, y, w, h, r, fill = values
            draw.rounded_rectangle((x*SCALE, y*SCALE, w*SCALE, h*SCALE), radius=r*SCALE, fill=fill)
        elif kind in ("text", "text_center"):
            x, y, content, size, fill, face, tracking = values
            font = ImageFont.truetype(BOLD if face == "bold" else MONO, size*SCALE)
            if kind == "text_center":
                x -= draw.textlength(content, font=font) / SCALE / 2
            if tracking:
                for character in content:
                    draw.text((x*SCALE, y*SCALE), character, font=font, fill=fill, anchor="ls")
                    x += draw.textlength(character, font=font) / SCALE + tracking
            else:
                draw.text((x*SCALE, y*SCALE), content, font=font, fill=fill, anchor="ls")
        elif kind == "line":
            x1, y1, x2, y2, color, stroke = values
            draw.line((x1*SCALE, y1*SCALE, x2*SCALE, y2*SCALE), fill=color, width=round(stroke*SCALE))
        elif kind == "circle":
            x, y, radius, fill, stroke, stroke_width = values
            draw.ellipse(((x-radius)*SCALE, (y-radius)*SCALE, (x+radius)*SCALE, (y+radius)*SCALE), fill=fill, outline=stroke, width=max(1, round(stroke_width*SCALE)))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def positions():
    # Pause at each stage, then fade out before resetting to the first stage.
    for frame in range(80):
        phase = frame / 79
        opacity = min(1, phase / 0.08, (1-phase) / 0.08)
        if phase < 0.12:
            yield 0, opacity
        elif phase < 0.44:
            t = (phase - 0.12) / 0.32
            yield 0.25 * (1 - math.cos(t * math.pi)), opacity
        elif phase < 0.56:
            yield 0.5, opacity
        elif phase < 0.88:
            t = (phase - 0.56) / 0.32
            yield 0.5 + 0.25 * (1 - math.cos(t * math.pi)), opacity
        else:
            yield 1, opacity


def generate(mobile=False):
    spec = layout(mobile)
    suffix = "-mobile" if mobile else ""
    name = f"profile-header{suffix}"
    (ASSETS/f"{name}.svg").write_text(svg(spec))
    samples = list(positions())
    palette = raster(spec, 0).quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    # Reserve the small accent's colors so text antialiasing cannot displace them.
    colors = palette.getpalette()
    background = tuple(bytes.fromhex(BACKGROUND[1:]))
    for offset, color in [(128, ACCENT), (144, HALO), (160, TRAIL), (176, TRAIL_FAINT)]:
        rgb = tuple(bytes.fromhex(color[1:]))
        for step in range(16):
            mix = step / 15
            value = [round(a * (1 - mix) + b * mix) for a, b in zip(rgb, background)]
            colors[(offset + step) * 3:(offset + step + 1) * 3] = value
    palette.putpalette(colors)
    frames = [raster(spec, position, opacity).quantize(palette=palette, dither=Image.Dither.NONE)
              for position, opacity in samples]
    # Keep the large flat background exact after GIF palette quantization.
    background_index = frames[0].getpixel((0, 0))
    colors[background_index * 3:(background_index + 1) * 3] = background
    for frame in frames:
        frame.putpalette(colors)
    frames[0].save(ASSETS/f"{name}.gif", save_all=True, append_images=frames[1:],
                   duration=75, loop=0, optimize=True, disposal=1)
    raster(spec, 1).save(ROOT.parent/f"{name}-preview.png")
    path = ASSETS/f"{name}.gif"
    with Image.open(path) as result:
        assert result.n_frames > 30
    print(f"{path.name}: {path.stat().st_size:,} bytes")


if __name__ == "__main__":
    generate()
    generate(mobile=True)
