"""POKÉLAB STUDIO — génère des Shorts/TikTok Pokémon sans montage manuel.

Lancer :  streamlit run app.py
"""
from __future__ import annotations

import re
import shutil
import time
from pathlib import Path

import streamlit as st

from src.subtitles import build_cues, write_ass
from src.video import THEMES, check_ffmpeg, render_video
from src.voice import engine_name, generate_voice, list_french_voices

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
WORK = OUT / ".work"

st.set_page_config(page_title="POKÉLAB STUDIO", page_icon="⚡", layout="wide")

st.markdown(
    """
<style>
:root { --accent:#FFD700; --accent2:#7C5CFF; }
.stApp { background: radial-gradient(1200px 600px at 10% -10%, #2a1660 0%, transparent 60%),
                     radial-gradient(900px 500px at 110% 10%, #5a4300 0%, transparent 55%), #0b0b14; color:#eee; }
h1.brand { font-weight:900; letter-spacing:.04em; margin:0;
           background:linear-gradient(90deg,#FFD700,#ff9f1a 40%,#b18cff); -webkit-background-clip:text; color:transparent; }
.sub { color:#a9a9c4; margin-top:-4px; }
.card { background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.08); border-radius:16px; padding:14px 16px; }
.stButton>button, .stDownloadButton>button { border-radius:12px; font-weight:800; border:0;
           background:linear-gradient(90deg,#FFD700,#ffb300); color:#111; }
.stButton>button:hover, .stDownloadButton>button:hover { filter:brightness(1.08); color:#000; }
textarea, input { background:#14141f !important; }
[data-testid="stHeader"] { background:transparent; }
video { max-height:72vh; border-radius:16px; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<h1 class="brand">⚡ POKÉLAB STUDIO</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub">Script → voix → sous-titres → vidéo 9:16 prête à publier. 100 % local, 0 €.</p>',
            unsafe_allow_html=True)

if not check_ffmpeg():
    st.error("FFmpeg est introuvable. Installe-le avec : `brew install ffmpeg`")
    st.stop()


def slug(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", s.lower()).strip()
    return re.sub(r"[\s_-]+", "_", s)[:40] or "video"


ss = st.session_state
ss.setdefault("wav", None)
ss.setdefault("dur", 0.0)
ss.setdefault("voice_key", None)
ss.setdefault("mp4", None)

left, right = st.columns([3, 2], gap="large")

with left:
    title = st.text_input("🎬 Titre de la vidéo", value="3 secrets sur les starters")
    script = st.text_area(
        "📝 Script (colle ici le script préparé avec Claude)",
        height=230,
        value=("Tu savais que les starters de type Feu, Eau et Plante forment un triangle parfait ?\n"
               "Le Feu bat la Plante, la Plante bat l'Eau, et l'Eau bat le Feu.\n"
               "Mais voici le vrai secret : dans la *première* génération, il y avait 151 créatures à découvrir.\n"
               "Et toi, tu choisis lequel ? Dis-le moi en commentaire !"),
        help="Astuce : entoure un mot d'astérisques (*mot*) pour le forcer en jaune. "
             "Nombres, MAJUSCULES et noms propres sont surlignés automatiquement.",
    )
    st.caption(f"{len(script.split())} mots · ~{len(script.split()) / 2.6:.0f} s estimées")

    with st.expander("🖼️ Médias personnels (optionnel — mode A)", expanded=False):
        media_files = st.file_uploader(
            "Images ou vidéos que tu possèdes (sinon : fond animé original, mode B)",
            type=["jpg", "jpeg", "png", "webp", "mp4", "mov", "m4v", "webm"],
            accept_multiple_files=True,
        )
    with st.expander("🎵 Musique (optionnel)", expanded=False):
        music_file = st.file_uploader("Fichier audio local libre de droits", type=["mp3", "wav", "m4a", "aac", "ogg"])
        music_vol = st.slider("Volume musique", 0.0, 0.5, 0.12, 0.01)
        st.caption("Utilise uniquement une musique dont tu as les droits (ex. bibliothèque audio YouTube).")

    with st.expander("⚙️ Réglages", expanded=False):
        voices = list_french_voices()
        voice = st.selectbox("Voix", voices, index=0) if voices else None
        st.caption(f"Moteur vocal : **{engine_name()}**")
        rate = st.slider("Débit (mots/min)", 140, 240, 185, 5)
        theme = st.selectbox("Thème du fond animé (mode B)", list(THEMES.keys()))

    c1, c2 = st.columns(2)
    gen_voice = c1.button("🎙️ 1. Générer la voix", use_container_width=True)
    gen_video = c2.button("🎬 2. Générer la vidéo", use_container_width=True, type="primary")

job = WORK / slug(title)
voice_key = (script, voice, rate)


def ensure_voice() -> None:
    if ss.wav and ss.voice_key == voice_key and Path(ss.wav).exists():
        return
    job.mkdir(parents=True, exist_ok=True)
    with st.spinner("Génération de la voix…"):
        wav, dur = generate_voice(script, job / "voice.wav", voice=voice, rate=rate)
    ss.wav, ss.dur, ss.voice_key = str(wav), dur, voice_key


try:
    if gen_voice:
        ss.voice_key = None
        ensure_voice()
        st.toast(f"Voix générée ({ss.dur:.1f} s)", icon="🎙️")

    if gen_video:
        if not script.strip():
            st.warning("Écris d'abord un script.")
            st.stop()
        t0 = time.time()
        ensure_voice()
        job.mkdir(parents=True, exist_ok=True)
        media_paths = []
        for i, f in enumerate(media_files or []):
            p = job / f"media_{i:02d}{Path(f.name).suffix.lower()}"
            p.write_bytes(f.getbuffer())
            media_paths.append(p)
        music_path = None
        if music_file:
            music_path = job / f"music{Path(music_file.name).suffix.lower()}"
            music_path.write_bytes(music_file.getbuffer())
        with st.spinner("Sous-titres + montage FFmpeg… (≈ 20 à 60 s)"):
            ass = write_ass(script, ss.dur, job / "subs.ass", title=title)
            out = OUT / f"{slug(title)}_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
            render_video(ss.wav, ass, out, ss.dur, media=media_paths, music=music_path,
                         theme=theme, music_volume=music_vol)
        ss.mp4 = str(out)
        st.toast(f"Vidéo prête en {time.time() - t0:.0f} s", icon="✅")
except Exception as e:  # affiche l'erreur proprement dans l'interface
    st.error(f"Erreur : {e}")

with right:
    st.markdown("#### 👀 Aperçu")
    if ss.mp4 and Path(ss.mp4).exists():
        st.video(ss.mp4)
        with open(ss.mp4, "rb") as fh:
            st.download_button("⬇️ Télécharger le MP4", fh, file_name=Path(ss.mp4).name,
                               mime="video/mp4", use_container_width=True)
        st.caption(f"Enregistré dans : `{Path(ss.mp4).relative_to(ROOT)}` · 1080×1920 · H.264/AAC")
    elif ss.wav and Path(ss.wav).exists():
        st.audio(ss.wav)
        st.caption(f"Narration : {ss.dur:.1f} s")
    else:
        st.markdown('<div class="card">Ta vidéo apparaîtra ici.<br><br>'
                    '<b>1.</b> Colle ton script<br><b>2.</b> (Optionnel) ajoute tes images<br>'
                    '<b>3.</b> Clique sur « Générer la vidéo »</div>', unsafe_allow_html=True)

    if ss.wav and ss.dur:
        with st.expander("Sous-titres (aperçu du découpage)"):
            for c in build_cues(script, ss.dur)[:40]:
                st.text(f"{c.start:5.1f}s  {' '.join(w.text for w in c.words)}")
