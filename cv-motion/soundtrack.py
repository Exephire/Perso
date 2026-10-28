"""Bande-son synthwave de 15 s (120 BPM) calée sur les transitions de cv-motion.html."""
import sys
import wave

import numpy as np

SR, DUR, BEAT = 44100, 15.0, 0.5
N = int(SR * DUR)
mix = np.zeros((N, 2))
rng = np.random.default_rng(1)


def add(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    mix[i:i + len(sig), 0] += sig * np.sqrt(0.5 * (1 - pan))
    mix[i:i + len(sig), 1] += sig * np.sqrt(0.5 * (1 + pan))


def tt(d):
    return np.arange(int(d * SR)) / SR


def lowpass(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (f / cutoff) ** 4), len(x))


def kick():
    t = tt(0.45)
    f = 45 + 110 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) + 0.3 * np.exp(-t * 400) * rng.standard_normal(len(t))


def hat(d=0.06):
    t = tt(d)
    return np.diff(rng.standard_normal(len(t) + 1)) * np.exp(-t * 70)


def snare():
    t = tt(0.25)
    return 0.6 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) + lowpass(rng.standard_normal(len(t)), 7000) * np.exp(-t * 16)


def saw(freq, d):
    t = tt(d)
    return sum(np.sin(2 * np.pi * freq * k * t) / k for k in range(1, 12)) * 0.6


def square(freq, d):
    t = tt(d)
    return np.sign(np.sin(2 * np.pi * freq * t)) * 0.5


def whoosh(d=0.7, rev=False):
    t = tt(d)
    env = np.sin(np.pi * t / d) ** 3
    sig = lowpass(rng.standard_normal(len(t)), 3500) * env
    return sig[::-1] if rev else sig


def impact():
    t = tt(1.6)
    boom = np.sin(2 * np.pi * np.cumsum(30 + 90 * np.exp(-t * 10)) / SR) * np.exp(-t * 2.5)
    crash = lowpass(np.diff(rng.standard_normal(len(t) + 1)), 9000) * np.exp(-t * 3) * 0.5
    return boom + crash


def blip(f=1400, d=0.07):
    t = tt(d)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 50)


def note(n):  # n en demi-tons depuis A4
    return 440 * 2 ** (n / 12)


# Intro : riser + montée
t = tt(2.5)
riser = lowpass(rng.standard_normal(len(t)), 6000) * (t / 2.5) ** 2.5 * 0.5
riser += np.sin(2 * np.pi * np.cumsum(180 + 900 * (t / 2.5) ** 2) / SR) * (t / 2.5) ** 2 * 0.25
add(riser, 0.0, 0.8)
for b in (0.1, 0.75, 1.2):  # sons UI de l'apparition
    add(blip(900 + b * 600, 0.12), b, 0.35)
add(impact(), 2.5, 1.0)

# Groove 2.5 -> 14
chords = [(-36, [0, 3, 7, 12]), (-40, [0, 4, 7, 12]), (-33, [0, 4, 7, 12]), (-38, [0, 4, 7, 12])]  # Am F C G
for k in range(int((14.0 - 2.5) / BEAT)):
    tb = 2.5 + k * BEAT
    add(kick(), tb, 0.9)
    add(hat(), tb + BEAT / 2, 0.18, 0.3)
    add(hat(0.03), tb + BEAT / 4, 0.08, -0.3)
    if k % 2 == 1:
        add(snare(), tb, 0.35)
for bar in range(6):
    t0 = 2.5 + bar * 2
    root, iv = chords[bar % 4]
    for s in range(16):  # basse en croches (pumping)
        ts = t0 + s * 0.125
        if ts >= 14.0:
            break
        b = saw(note(root), 0.12) * np.exp(-tt(0.12) * 10)
        add(lowpass(b, 900), ts, 0.28)
    if t0 >= 6.0:  # arpège dès la scène STATS
        for s in range(16):
            ts = t0 + s * 0.125
            if ts >= 14.0:
                break
            a = square(note(root + 24 + iv[s % 4]), 0.1) * np.exp(-tt(0.1) * 22)
            add(lowpass(a, 4000), ts, 0.07, 0.4 if s % 2 else -0.4)
    pad = sum(saw(note(root + 12 + i), 2.0) for i in iv) * np.minimum(1, tt(2.0) * 4) * np.minimum(1, (2.0 - tt(2.0)) * 4)
    add(lowpass(pad, 1500), t0, 0.035)

# Transitions
for tc in (6.0, 9.5, 12.5):
    add(whoosh(0.7), tc - 0.4, 0.45)
    add(impact()[: SR // 2], tc, 0.35)
# Barres de compétences / cartes / mots
for i in range(4):
    add(blip(1100 + i * 220), 6.5 + i * 0.17, 0.3)
for i in range(3):
    add(blip(700 + i * 300, 0.1), 9.8 + i * 0.16, 0.3)
for i in range(3):
    add(blip(1500 + i * 250, 0.09), 11.0 + i * 0.3, 0.3)

# XP qui monte puis LEVEL UP
t = tt(0.85)
xp = np.sign(np.sin(2 * np.pi * np.cumsum(400 + 1200 * (t / 0.85) ** 2) / SR)) * 0.5 * (t / 0.85)
add(lowpass(xp, 5000), 13.15, 0.08)
for i, n in enumerate([3, 7, 10, 15, 19]):  # C E G C E (jingle 8-bit)
    add(square(note(n), 0.09) * np.exp(-tt(0.09) * 8), 14.0 + i * 0.07, 0.16)
chord = sum(square(note(n), 1.0) for n in (15, 19, 22, 27)) * np.exp(-tt(1.0) * 3)
add(lowpass(chord, 6000), 14.35, 0.06)
add(impact(), 14.0, 0.9)

# Master
fade = np.ones(N)
fade[-int(0.35 * SR):] = np.linspace(1, 0, int(0.35 * SR))
mix *= fade[:, None]
mix = np.tanh(mix * 1.4)
mix /= np.abs(mix).max() / 0.9

out = sys.argv[1] if len(sys.argv) > 1 else 'soundtrack.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('ok', out)
