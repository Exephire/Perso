"""Montage vidéo vertical 1080x1920 avec FFmpeg.

Mode A : images / vidéos personnelles importées (Ken Burns + fondu).
Mode B : fond graphique animé 100 % original (dégradé, grille hexagonale,
         orbes lumineux) généré localement — aucun contenu protégé.
"""
from __future__ import annotations

import math
import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H, FPS = 1080, 1920, 30
ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "assets" / "fonts"

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}

# Palettes originales inspirées des « types » (couleurs génériques).
THEMES = {
    "Électrik": {"grad": ["0x1a0b3d", "0x3b1d7a", "0x6b4a00"], "orb1": (255, 215, 0), "orb2": (120, 80, 255)},
    "Feu": {"grad": ["0x2b0505", "0x7a1d0b", "0x3d1a00"], "orb1": (255, 120, 30), "orb2": (255, 210, 60)},
    "Eau": {"grad": ["0x03142b", "0x0b3d7a", "0x052a3d"], "orb1": (60, 170, 255), "orb2": (0, 255, 220)},
    "Plante": {"grad": ["0x04210d", "0x0f5a2a", "0x1f3d05"], "orb1": (90, 230, 120), "orb2": (220, 255, 90)},
    "Psy": {"grad": ["0x2b0530", "0x6a0b7a", "0x1a0b4d"], "orb1": (255, 90, 200), "orb2": (150, 120, 255)},
    "Spectre": {"grad": ["0x0a0518", "0x24104a", "0x05101f"], "orb1": (170, 90, 255), "orb2": (60, 255, 200)},
}


def check_ffmpeg() -> bool:
    return bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError("FFmpeg a échoué :\n" + res.stderr[-2500:])


# ---------- Éléments graphiques générés localement (PIL) ----------

def _hex_pattern(path: Path, color=(255, 255, 255), period: int = 240) -> int:
    """Grille hexagonale transparente, haute de H+period pour un défilement en boucle."""
    r = 60
    hh = math.sqrt(3) * r
    img = Image.new("RGBA", (W, H + period), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    col = 0
    x = -r
    while x < W + 2 * r:
        y = -hh + (hh / 2 if col % 2 else 0)
        while y < H + period + hh:
            pts = [(x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))) for a in range(0, 360, 60)]
            d.polygon(pts, outline=color + (28,), width=2)
            y += hh
        x += 1.5 * r
        col += 1
    img.save(path)
    # La grille se répète tous les 2*hh pixels verticalement.
    return int(round(2 * hh))


def _orb(path: Path, rgb, size: int = 900) -> None:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size // 2
    for i in range(c, 0, -6):
        a = int(140 * (1 - i / c) ** 2)
        d.ellipse([c - i, c - i, c + i, c + i], fill=rgb + (a,))
    img.filter(ImageFilter.GaussianBlur(18)).save(path)


def _vignette(path: Path) -> None:
    """Assombrit le haut et le bas pour la lisibilité du titre et des sous-titres."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(H):
        top = max(0.0, 1 - y / 520) * 150
        bot = max(0.0, (y - 1050) / (H - 1050)) * 190
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(max(top, bot))))
    img.save(path)


# ---------- Mode A : segments à partir des médias importés ----------

def _media_segment(src: Path, out: Path, dur: float, idx: int) -> None:
    frames = max(int(dur * FPS), 1)
    cover = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
    fade = f"fade=t=in:st=0:d=0.3"
    if src.suffix.lower() in IMAGE_EXT:
        # Ken Burns : zoom avant / arrière en alternance, léger panoramique.
        if idx % 2 == 0:
            z = "min(1+0.12*on/{f},1.12)".format(f=frames)
        else:
            z = "max(1.12-0.12*on/{f},1)".format(f=frames)
        xexpr = "iw/2-(iw/zoom/2)" + ("+on*0.15" if idx % 3 == 1 else "")
        vf = (f"scale={int(W*1.25)}:{int(H*1.25)}:force_original_aspect_ratio=increase,"
              f"crop={int(W*1.25)}:{int(H*1.25)},"
              f"zoompan=z='{z}':x='{xexpr}':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},"
              f"setsar=1,{fade}")
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(src), "-t", f"{dur:.3f}", "-vf", vf]
    else:
        cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(src), "-t", f"{dur:.3f}",
               "-vf", f"{cover},fps={FPS},{fade}"]
    cmd += ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)]
    _run(cmd)


def _build_media_base(media: list[Path], dur: float, work: Path) -> Path:
    seg_dur = dur / len(media)
    segs = []
    for i, m in enumerate(media):
        seg = work / f"seg_{i:02d}.mp4"
        _media_segment(m, seg, seg_dur + 0.05, i)
        segs.append(seg)
    lst = work / "segments.txt"
    lst.write_text("".join(f"file '{s.name}'\n" for s in segs), encoding="utf-8")
    base = work / "base.mp4"
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst.name, "-c", "copy", base.name], cwd=work)
    return base


# ---------- Rendu final ----------

def render_video(
    narration: str | Path,
    ass_file: str | Path,
    out_mp4: str | Path,
    duration: float,
    media: list[str | Path] | None = None,
    music: str | Path | None = None,
    theme: str = "Électrik",
    music_volume: float = 0.12,
) -> Path:
    narration, ass_file, out_mp4 = Path(narration).resolve(), Path(ass_file).resolve(), Path(out_mp4).resolve()
    work = ass_file.parent
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    media = [Path(m) for m in (media or []) if Path(m).suffix.lower() in IMAGE_EXT | VIDEO_EXT]
    pal = THEMES.get(theme, THEMES["Électrik"])
    D = f"{duration:.3f}"

    _vignette(work / "vignette.png")
    inputs: list[str] = []
    fc: list[str] = []

    if media:  # ---- Mode A
        base = _build_media_base(media, duration, work)
        inputs += ["-i", str(base)]
        fc.append("[0:v]eq=saturation=1.08:contrast=1.04[bg]")
        n = 1
    else:  # ---- Mode B : fond original animé
        period = _hex_pattern(work / "hex.png")
        _orb(work / "orb1.png", pal["orb1"])
        _orb(work / "orb2.png", pal["orb2"], 700)
        g = pal["grad"]
        inputs += ["-f", "lavfi", "-i",
                   f"gradients=s={W}x{H}:r={FPS}:d={D}:c0={g[0]}:c1={g[1]}:c2={g[2]}:nb_colors=3:speed=0.015:type=linear"]
        inputs += ["-loop", "1", "-framerate", str(FPS), "-i", str(work / "hex.png")]
        inputs += ["-loop", "1", "-framerate", str(FPS), "-i", str(work / "orb1.png")]
        inputs += ["-loop", "1", "-framerate", str(FPS), "-i", str(work / "orb2.png")]
        fc.append(f"[0:v][1:v]overlay=x=0:y='-mod(t*45,{period})':shortest=1[b1]")
        fc.append("[b1][2:v]overlay=x='W/2-w/2+260*sin(t*0.6)':y='H*0.40-h/2+220*cos(t*0.45)':shortest=1[b2]")
        fc.append("[b2][3:v]overlay=x='W/2-w/2-300*cos(t*0.5)':y='H*0.62-h/2+180*sin(t*0.7)':shortest=1[bg]")
        n = 4

    inputs += ["-loop", "1", "-framerate", str(FPS), "-i", str(work / "vignette.png")]
    vig = n
    n += 1
    # Barre de progression (en haut, hors zone d'interface TikTok).
    inputs += ["-f", "lavfi", "-i", f"color=c=0xFFD700:s={W}x10:r={FPS}:d={D}"]
    bar = n
    n += 1
    inputs += ["-i", str(narration)]
    voice = n
    n += 1

    fonts = f":fontsdir={os.path.relpath(FONTS_DIR, work)}" if FONTS_DIR.is_dir() and any(FONTS_DIR.iterdir()) else ""
    fc.append(f"[bg][{vig}:v]overlay=0:0:shortest=1[v1]")
    fc.append(f"[v1][{bar}:v]overlay=x='-W+W*t/{D}':y=0:shortest=1[v2]")
    fc.append(f"[v2]ass={ass_file.name}{fonts},format=yuv420p[vout]")

    if music:
        inputs += ["-stream_loop", "-1", "-i", str(Path(music).resolve())]
        fc.append(f"[{n}:a]volume={music_volume},afade=t=out:st={max(duration-1.5,0):.2f}:d=1.5[mus]")
        fc.append(f"[{voice}:a][mus]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]")
        n += 1
    else:
        fc.append(f"[{voice}:a]anull[aout]")

    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc),
           "-map", "[vout]", "-map", "[aout]", "-t", D,
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
           "-movflags", "+faststart", str(out_mp4)]
    _run(cmd, cwd=work)
    return out_mp4


def make_video(title: str, script: str, out_name: str, media=None, music=None, theme="Électrik",
               voice: str | None = None, rate: int = 185, work_dir: str | Path | None = None) -> Path:
    """Pipeline complet : voix -> sous-titres -> montage. Utilisable sans interface."""
    from .subtitles import write_ass
    from .voice import generate_voice

    work = Path(work_dir or ROOT / "output" / ".work" / Path(out_name).stem)
    work.mkdir(parents=True, exist_ok=True)
    wav, dur = generate_voice(script, work / "voice.wav", voice=voice, rate=rate)
    ass = write_ass(script, dur, work / "subs.ass", title=title)
    return render_video(wav, ass, ROOT / "output" / out_name, dur, media=media, music=music, theme=theme)
