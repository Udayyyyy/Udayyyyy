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
PAPER = "#F2F0E9"
INK = "#191D20"
MUTED = "#71756F"
RULE = "#C7C9C0"
ACCENT = "#C95036"
HALO = "#EBCBBE"
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


def primitives(spec, progress):
    width, height = spec["size"]
    start, end, y = spec["axis"]
    shapes = [("rect", (0, 0, width, height, 6, PAPER))]
    shapes += [("text", item) for item in spec["texts"]]
    shapes += [("text_center", (x, 86, label, 17, MUTED, "mono", 0))
               for x, label in spec["labels"]]
    shapes.append(("line", (start, y, end, y, RULE, 1.6)))
    for x in [start, (start + end) / 2, end]:
        shapes.append(("circle", (x, y, 4.5, PAPER, MUTED, 1.4)))
    x = start + (end - start) * progress
    shapes.append(("circle", (x, y, 9, HALO, None, 0)))
    shapes.append(("circle", (x, y, 4.2, ACCENT, None, 0)))
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


def raster(spec, progress):
    width, height = spec["size"]
    image = Image.new("RGB", (width * SCALE, height * SCALE), PAPER)
    draw = ImageDraw.Draw(image)
    for kind, values in primitives(spec, progress):
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
    # Pause at each stage; all movement is limited to the small signal marker.
    for frame in range(80):
        phase = frame / 79
        if phase < 0.12:
            yield 0
        elif phase < 0.44:
            t = (phase - 0.12) / 0.32
            yield 0.25 * (1 - math.cos(t * math.pi))
        elif phase < 0.56:
            yield 0.5
        elif phase < 0.88:
            t = (phase - 0.56) / 0.32
            yield 0.5 + 0.25 * (1 - math.cos(t * math.pi))
        else:
            yield 1


def generate(mobile=False):
    spec = layout(mobile)
    suffix = "-mobile" if mobile else ""
    name = f"profile-header{suffix}"
    (ASSETS/f"{name}.svg").write_text(svg(spec))
    samples = list(positions())
    palette = raster(spec, 0).quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    frames = [raster(spec, position).quantize(palette=palette, dither=Image.Dither.NONE)
              for position in samples]
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
