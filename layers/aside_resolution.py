"""Aside (not a layer): why resolution = 1 / window duration.

One pure 262 Hz tone. Probe it at 262 and at nearby wrong frequencies,
using windows of different LENGTHS. Watch the wrong answers die off
exactly as their phase drift passes one full cycle.
"""
import numpy as np

RATE, TONE = 44100, 262.0

def energy_at(x, freq):
    t = np.arange(len(x)) / RATE
    return abs(np.sum(x * np.exp(-2j * np.pi * freq * t))) / len(x)

probes = [262.0, 266.0, 272.0, 282.0]
print(f"pure {TONE} Hz tone, probed at {probes}\n")
print(f"{'window':>9} {'res 1/T':>8} | " + " ".join(f"{p:>7.0f}Hz" for p in probes))
print("-" * 58)
for T in [0.023, 0.093, 0.372, 1.0]:
    x = np.sin(2 * np.pi * TONE * np.arange(int(RATE * T)) / RATE)
    row = " ".join(f"{energy_at(x, p):>9.3f}" for p in probes)
    print(f"{T*1000:>7.0f}ms {1/T:>7.1f}Hz | {row}")

print("\nphase drift (cycles) of each probe vs the true tone over the window:")
print(f"{'window':>9} | " + " ".join(f"{p:>7.0f}Hz" for p in probes))
print("-" * 45)
for T in [0.023, 0.093, 0.372, 1.0]:
    row = " ".join(f"{abs(p - TONE) * T:>9.2f}" for p in probes)
    print(f"{T*1000:>7.0f}ms | {row}")
