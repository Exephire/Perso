"""Génère la vidéo de démonstration sans passer par l'interface."""
import time
from src.video import make_video

TITLE = "3 secrets sur les starters"
SCRIPT = """Tu savais que les starters de type Feu, Eau et Plante forment un triangle parfait ?
Le Feu bat la Plante, la Plante bat l'Eau, et l'Eau bat le Feu.
Mais voici le vrai secret : dans la *première* génération, il y avait 151 créatures à découvrir.
Et toi, tu choisis lequel ? Dis-le moi en commentaire !"""

if __name__ == "__main__":
    t = time.time()
    out = make_video(TITLE, SCRIPT, "demo_pokelab.mp4", theme="Électrik")
    print(f"OK -> {out} ({time.time() - t:.1f}s)")
