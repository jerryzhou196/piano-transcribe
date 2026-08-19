"""Aside: one window length cannot serve the whole keyboard.

Play two ADJACENT notes at the bottom, and two ADJACENT notes at the top.
Probe both with the same 4096-sample window and see what it can resolve.
"""
import numpy as np

RATE = 44100
NAMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
f = lambda m: 440.0 * 2 ** ((m - 69) / 12)
name = lambda m: f"{NAMES[m % 12]}{m // 12 - 1}"

def probe(x, midis, N):
    t = np.arange(N) / RATE
    fr = np.array([f(m) for m in midis])
    return np.abs(np.exp(-2j * np.pi * fr[:, None] * t) @ x[:N]) / N

def show(title, played, midis, N):
    t = np.arange(N) / RATE
    x = sum(np.sin(2 * np.pi * f(m) * t) for m in played) / len(played)
    mags = probe(x, midis, N)
    print(f"\n{title}   (played: {[name(m) for m in played]}, window {N} = {N/RATE*1000:.0f}ms)")
    for m, v in zip(midis, mags):
        star = "  <-- played" if m in played else ""
        print(f"  {name(m):>4} {f(m):8.1f}Hz |{'#' * int(v * 120):<45}{star}")

show("BOTTOM: two adjacent keys", [21, 22], range(21, 27), 4096)
show("TOP: two adjacent keys",    [93, 94], range(93, 99), 4096)
show("TOP again, 8x shorter window", [93, 94], range(93, 99), 512)
