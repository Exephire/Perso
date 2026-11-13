#!/bin/bash
# Double-clic sur macOS pour lancer POKÉLAB STUDIO
cd "$(dirname "$0")"
command -v ffmpeg >/dev/null || { echo "FFmpeg manquant -> brew install ffmpeg"; read -r; exit 1; }
python3 -c "import streamlit" 2>/dev/null || python3 -m pip install --user -r requirements.txt
python3 -m streamlit run app.py
