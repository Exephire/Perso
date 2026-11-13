# ⚡ POKÉLAB STUDIO

Génère des vidéos **TikTok / YouTube Shorts** Pokémon (1080×1920, H.264/AAC) à partir d'un simple script.
100 % local · 0 € · aucune API · aucun compte.

## Installation sur Mac (une seule fois)

```bash
# 1. FFmpeg (gratuit) — si `ffmpeg -version` ne répond pas :
brew install ffmpeg          # Homebrew : https://brew.sh

# 2. Dépendances Python
cd POKELAB
python3 -m pip install -r requirements.txt
```

`say` (voix française) est déjà inclus dans macOS. Pour une meilleure voix :
**Réglages Système → Accessibilité → Contenu énoncé → Voix du système → Gérer les voix → Français** (ex. *Thomas* ou *Amélie*, version « améliorée »).

## Lancer

```bash
cd POKELAB
python3 -m streamlit run app.py
```
→ l'app s'ouvre sur **http://localhost:8501**. (Ou double-clic sur `lancer.command`.)

## Utilisation

1. Colle ton script (préparé avec Claude).
2. Optionnel : importe tes images/vidéos perso (**mode A**). Sans médias → fond animé original (**mode B**, 6 thèmes).
3. Optionnel : une musique locale dont tu as les droits.
4. Clique **Générer la vidéo** → aperçu + bouton **Télécharger le MP4**. Le fichier est aussi dans `output/`.

**Astuces script**
- `*mot*` → force le mot en jaune.
- Nombres, MAJUSCULES et noms propres sont surlignés automatiquement.
- Phrases courtes = sous-titres plus dynamiques.

## Sans interface

```bash
python3 demo.py                   # génère output/demo_pokelab.mp4
python3 -m tests.test_pipeline    # tests (mode A, mode B, sous-titres)
```

## Limites du MVP (assumées)

- Synchro des sous-titres **proportionnelle** (longueur des mots + pauses de ponctuation), pas mot à mot.
- Aucun média Pokémon n'est téléchargé : utilise uniquement des contenus que tu possèdes ou as le droit d'utiliser.
- Sous Linux (hors Mac), la voix de secours est `espeak-ng` (plus robotique).

## Structure

```
POKELAB/
├── app.py              # interface Streamlit
├── demo.py             # vidéo de démo en ligne de commande
├── src/voice.py        # say / espeak-ng -> WAV
├── src/subtitles.py    # sous-titres ASS (blanc + jaune, pop)
├── src/video.py        # montage FFmpeg (modes A/B)
├── tests/              # tests de bout en bout
├── assets/             # (optionnel) assets/fonts/ pour une police perso
└── output/             # vidéos exportées
```
