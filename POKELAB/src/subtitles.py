"""Sous-titres style TikTok au format ASS (rendus par FFmpeg/libass).

Synchronisation MVP : répartition proportionnelle à la longueur des mots
(+ pauses sur la ponctuation) sur la durée réelle de la narration.
Ce n'est PAS une synchro mot à mot parfaite, mais c'est très correct
pour une voix de synthèse au débit régulier.

Mots en jaune :
- les mots entourés d'astérisques dans le script : *Dracaufeu*
- les nombres (151, 2024, 50%…)
- les mots EN MAJUSCULES
- les noms propres (majuscule hors début de phrase)
"""
from __future__ import annotations

import platform
import re
from dataclasses import dataclass
from pathlib import Path

W, H = 1080, 1920
WHITE = "&H00FFFFFF&"
YELLOW = "&H0000D7FF&"  # ASS = BGR -> #FFD700

DEFAULT_FONT = "Arial Black" if platform.system() == "Darwin" else "Inter Black"


@dataclass
class Word:
    text: str          # mot affiché (sans astérisques)
    key: bool          # mot important -> jaune
    pause: float       # poids de pause après le mot (ponctuation)


@dataclass
class Cue:
    start: float
    end: float
    words: list[Word]


def parse_words(script: str) -> list[Word]:
    words: list[Word] = []
    sentence_start = True
    in_star = False
    for raw in script.replace("\n", " ").split():
        starts_star = raw.startswith("*")
        ends_star = raw.rstrip(".,!?;:…»)\"'").endswith("*")
        flagged = in_star or starts_star
        if starts_star and not ends_star:
            in_star = True
        if ends_star:
            in_star = False
        text = raw.replace("*", "")
        if not text:
            continue
        core = re.sub(r"[^\wÀ-ÿ%-]", "", re.split(r"['’]", text)[-1])
        is_num = bool(re.search(r"\d", core))
        is_caps = len(core) >= 2 and core.isupper()
        is_proper = (not sentence_start) and core[:1].isupper()
        key = flagged or is_num or is_caps or is_proper
        pause = 0.0
        if re.search(r"[.!?…]$", text):
            pause, sentence_start = 6.0, True
        elif re.search(r"[,;:]$", text):
            pause, sentence_start = 3.0, False
        else:
            sentence_start = False
        words.append(Word(text, key, pause))
    return words


def build_cues(script: str, duration: float, max_words: int = 3, lead: float = 0.15, tail: float = 0.6) -> list[Cue]:
    """Regroupe les mots en blocs de 1 à `max_words` et leur attribue un timing."""
    words = parse_words(script)
    if not words:
        return []
    groups: list[list[Word]] = [[]]
    for w in words:
        groups[-1].append(w)
        if len(groups[-1]) >= max_words or w.pause > 0 or len(" ".join(x.text for x in groups[-1])) > 18:
            groups.append([])
    groups = [g for g in groups if g]

    def weight(g: list[Word]) -> float:
        return sum(len(w.text) + 2 for w in g) + sum(w.pause for w in g)

    speech = max(duration - lead - tail, 0.5)
    total = sum(weight(g) for g in groups)
    cues, t = [], lead
    for g in groups:
        d = speech * weight(g) / total
        cues.append(Cue(t, t + d, g))
        t += d
    return cues


def _ts(t: float) -> str:
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("{", "(").replace("}", ")")


def write_ass(script: str, duration: float, out_path: str | Path, title: str = "", font: str = DEFAULT_FONT) -> Path:
    out_path = Path(out_path)
    cues = build_cues(script, duration)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{font},96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,3,2,90,90,560,1
Style: Title,{font},78,&H00FFFFFF,&H00FFFFFF,&H00301A0E,&H96000000,-1,0,0,0,100,100,0,0,1,6,0,8,80,80,230,1
Style: Brand,{font},34,&H0000D7FF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,4,0,1,3,0,8,80,80,150,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    if title:
        lines.append(f"Dialogue: 2,{_ts(0)},{_ts(duration)},Brand,,0,0,0,,{{\\fad(400,0)}}POKÉLAB STUDIO")
        lines.append(
            f"Dialogue: 2,{_ts(0)},{_ts(duration)},Title,,0,0,0,,"
            f"{{\\fad(300,0)\\fscx70\\fscy70\\t(0,250,\\fscx108\\fscy108)\\t(250,400,\\fscx100\\fscy100)}}{_esc(title.upper())}"
        )
    for c in cues:
        parts = []
        for w in c.words:
            col = YELLOW if w.key else WHITE
            parts.append(f"{{\\c{col}}}{_esc(w.text)}")
        pop = "{\\fscx78\\fscy78\\t(0,110,\\fscx106\\fscy106)\\t(110,180,\\fscx100\\fscy100)}"
        lines.append(f"Dialogue: 1,{_ts(c.start)},{_ts(c.end)},Sub,,0,0,0,,{pop}{' '.join(parts)}")
    out_path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
    return out_path
