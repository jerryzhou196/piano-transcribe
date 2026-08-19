"""Layer 3: 'how much of frequency f?' = correlate the signal with a test sine.

This IS the DFT. numpy.fft just does it for all frequencies at once, quickly.
"""
import math, struct, wave

with wave.open("chord.wav", "rb") as w:
    rate, n = w.getframerate(), w.getnframes()
    samples = [v / 32767 for v in struct.unpack(f"<{n}h", w.readframes(n))]

WINDOW = 4096                      # ~93 ms of audio
chunk = samples[:WINDOW]

def energy_at(x, freq, rate):
    """Correlate x with a test sine AND cosine at freq; return the magnitude."""
    re = im = 0.0
    for i, v in enumerate(x):
        angle = 2 * math.pi * freq * i / rate
        re += v * math.cos(angle)      # in-phase part
        im += v * math.sin(angle)      # quarter-turn-shifted part
    return math.hypot(re, im) / len(x)  # both, so starting phase doesn't matter

print("single frequencies, probed one at a time:")
for f in [200.0, 261.63, 300.0, 329.63, 350.0, 392.0, 440.0]:
    print(f"  {f:7.2f} Hz -> {energy_at(chunk, f, rate):.4f}")

print("\nsweep 200-450 Hz:")
for f in range(200, 451, 4):
    e = energy_at(chunk, f, rate)
    print(f"{f:4d} |{'#' * int(e * 300)}")
