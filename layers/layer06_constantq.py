"""Layer 6: constant-Q -- window length per key, so each sees ~Q cycles.

Low keys look at ~900ms, high keys at ~6ms. Same number of wiggles either way.
"""
import struct, wave
import numpy as np

RATE = 44100
NAMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
MIDI = np.arange(21, 109)
FREQS = 440.0 * 2 ** ((MIDI - 69) / 12)
name = lambda m: f"{NAMES[m % 12]}{m // 12 - 1}"

def fixed_keybank(x, N=4096):
    t = np.arange(N) / RATE
    return np.abs(np.exp(-2j * np.pi * FREQS[:, None] * t) @ x[:N]) / N

def cq_keybank(x, Q=24):
    out = np.zeros(88)
    for k, f in enumerate(FREQS):
        N = min(int(Q * RATE / f), len(x))      # this key's own window
        t = np.arange(N) / RATE
        out[k] = abs(np.exp(-2j * np.pi * f * t) @ x[:N]) / N
    return out

print("window length per key at Q=24:")
for m in [21, 45, 69, 93, 108]:
    f = 440.0 * 2 ** ((m - 69) / 12)
    N = int(24 * RATE / f)
    print(f"  {name(m):>4} {f:8.1f}Hz -> {N:6d} samples = {N/RATE*1000:7.1f} ms")

def compare(title, x, lo, hi, played):
    fix, cq = fixed_keybank(x), cq_keybank(x)
    print(f"\n{title}   played: {[name(m) for m in played]}")
    print(f"{'key':>5} | {'fixed 93ms':<26} | {'constant-Q':<26}")
    for i in np.where((MIDI >= lo) & (MIDI <= hi))[0]:
        m = MIDI[i]
        s = " *" if m in played else ""
        print(f"{name(m):>5} | {'#' * int(fix[i]*55):<26} | {'#' * int(cq[i]*55):<26}{s}")

t = np.arange(int(RATE * 2)) / RATE
bass = sum(np.sin(2*np.pi*440.0*2**((m-69)/12)*t) for m in [21, 22]) / 2
compare("BASS DYAD", bass, 21, 27, [21, 22])

with wave.open("chord.wav", "rb") as w:
    n = w.getnframes()
    chord = np.array(struct.unpack(f"<{n}h", w.readframes(n))) / 32767
compare("C MAJOR", chord, 59, 68, [60, 64, 67])
