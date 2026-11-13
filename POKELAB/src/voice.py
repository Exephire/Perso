"""Génération vocale 100 % locale.

- macOS : commande `say` (voix française si disponible).
- Linux : repli sur `espeak-ng` (gratuit) pour pouvoir tester hors Mac.
Le résultat est toujours converti en WAV 44,1 kHz mono, lisible par FFmpeg.
"""
from __future__ import annotations

import platform
import re
import shutil
import subprocess
from pathlib import Path

# Voix françaises macOS, par ordre de préférence.
PREFERRED_FR_VOICES = ["Thomas", "Amélie", "Audrey", "Aurélie", "Marie", "Daniel (French (France))"]


def clean_for_speech(text: str) -> str:
    """Retire les marqueurs de mise en forme (*mot*) avant la lecture."""
    text = text.replace("*", "")
    return re.sub(r"\s+", " ", text).strip()


def list_french_voices() -> list[str]:
    """Liste les voix françaises de `say` (macOS uniquement)."""
    if not shutil.which("say"):
        return []
    try:
        out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return []
    voices = []
    for line in out.splitlines():
        m = re.match(r"^(.+?)\s{2,}(fr[_-][A-Z]{2})", line)
        if m:
            voices.append(m.group(1).strip())
    # Met les voix préférées en premier.
    voices.sort(key=lambda v: PREFERRED_FR_VOICES.index(v) if v in PREFERRED_FR_VOICES else 99)
    return voices


def engine_name() -> str:
    if shutil.which("say"):
        return "macOS say"
    if shutil.which("espeak-ng"):
        return "espeak-ng (repli Linux)"
    return "aucun"


def audio_duration(path: str | Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def generate_voice(text: str, out_wav: str | Path, voice: str | None = None, rate: int = 185) -> tuple[Path, float]:
    """Génère la narration. Retourne (chemin_wav, durée_en_secondes)."""
    out_wav = Path(out_wav)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    speech = clean_for_speech(text)
    if not speech:
        raise ValueError("Le script est vide.")

    txt_file = out_wav.with_suffix(".txt")
    txt_file.write_text(speech, encoding="utf-8")
    raw = out_wav.with_suffix(".raw.aiff")

    if shutil.which("say"):
        if voice is None:
            fr = list_french_voices()
            voice = fr[0] if fr else None
        cmd = ["say", "-r", str(rate), "-o", str(raw), "-f", str(txt_file)]
        if voice:
            cmd[1:1] = ["-v", voice]
        subprocess.run(cmd, check=True)
    elif shutil.which("espeak-ng"):
        raw = out_wav.with_suffix(".raw.wav")
        # espeak-ng parle en mots/minute ; ~175 est naturel.
        subprocess.run(["espeak-ng", "-v", "fr-fr", "-s", str(int(rate * 0.9)), "-f", str(txt_file), "-w", str(raw)], check=True)
    else:
        raise RuntimeError("Aucun moteur vocal trouvé (ni `say` ni `espeak-ng`).")

    # Conversion en WAV propre + léger silence à la fin.
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af", "apad=pad_dur=0.6",
         "-ar", "44100", "-ac", "1", str(out_wav)],
        check=True,
    )
    raw.unlink(missing_ok=True)
    txt_file.unlink(missing_ok=True)
    return out_wav, audio_duration(out_wav)
