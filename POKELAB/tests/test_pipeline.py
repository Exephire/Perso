"""Tests rapides : python3 -m tests.test_pipeline"""
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from src.subtitles import build_cues, parse_words, write_ass
from src.video import render_video
from src.voice import generate_voice


def probe(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(p)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def check_mp4(p, min_dur):
    info = probe(p)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next(s for s in info["streams"] if s["codec_type"] == "audio")
    assert (v["codec_name"], v["width"], v["height"]) == ("h264", 1080, 1920), v
    assert a["codec_name"] == "aac", a
    assert float(info["format"]["duration"]) >= min_dur


def test_subtitles():
    words = parse_words("le Feu bat l'Eau, il y avait 151 *super* créatures. ADORE")
    keys = {w.text for w in words if w.key}
    assert keys == {"Feu", "l'Eau,", "151", "super", "ADORE"}, keys
    cues = build_cues("un deux trois quatre cinq six sept.", 10.0)
    assert abs(cues[-1].end - (10.0 - 0.6)) < 1e-6 and cues[0].start > 0
    assert all(a.end <= b.start + 1e-9 for a, b in zip(cues, cues[1:]))


def test_mode_a_with_media_and_music():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        for i, col in enumerate([(200, 40, 40), (40, 90, 200)]):
            im = Image.new("RGB", (1600, 1200), col)
            ImageDraw.Draw(im).ellipse([500, 300, 1100, 900], fill=(255, 220, 0))
            im.save(d / f"img{i}.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=1280x720:d=2", d / "clip.mp4"], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=f=330:d=3", d / "music.wav"], check=True)
        script = "Voici un test du mode A avec 3 médias personnels et une *musique* locale."
        wav, dur = generate_voice(script, d / "voice.wav")
        ass = write_ass(script, dur, d / "subs.ass", title="Test mode A")
        out = render_video(wav, ass, d / "out.mp4", dur,
                           media=[d / "img0.jpg", d / "clip.mp4", d / "img1.jpg"], music=d / "music.wav")
        check_mp4(out, dur - 0.2)


def test_mode_b():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        script = "Test du mode B avec un fond animé original."
        wav, dur = generate_voice(script, d / "voice.wav")
        ass = write_ass(script, dur, d / "subs.ass", title="Test mode B")
        check_mp4(render_video(wav, ass, d / "out.mp4", dur, theme="Eau"), dur - 0.2)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"✅ {name}")
