"""Layer 5: 88 probes, one per piano key -- not 2049 bins on an arbitrary grid.

Layer 3's correlator accepts any frequency. So ask it about the notes.
"""
import struct, wave
import numpy as np

NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MIDI = np.arange(21, 109)  # A0 .. C8 = 88 keys
FREQS = 440.0 * 2 ** ((MIDI - 69) / 12)  # equal temperament


def name(m):
    return f"{NAMES[m % 12]}{m // 12 - 1}"


with wave.open("chord.wav", "rb") as w:
    rate, n = w.getframerate(), w.getnframes()
    x = np.array(struct.unpack(f"<{n}h", w.readframes(n))) / 32767

N = 4096
chunk = x[:N]
t = np.arange(N) / rate

# one correlation per key: 88 probes x N samples
freq_col = FREQS[:, None]  # (88, 1)  one frequency per row
time_row = t[None, :]  # (1, N)   one time per column
cycles = freq_col * time_row  # (88, N)  cycles at each (key, sample)
probes = np.exp(-2j * np.pi * cycles)  # complex sinusoid per key
keybank = np.abs(probes @ chunk) / N  # 88 magnitudes, same as layer 3

print(f"{name(MIDI[0])}={FREQS[0]:.2f}Hz .. {name(MIDI[-1])}={FREQS[-1]:.2f}Hz")
print(f"neighbours differ by 5.9%, never by a fixed number of Hz\n")

print("loudest keys:")
for i in np.argsort(keybank)[::-1][:6]:
    print(f"  {name(MIDI[i]):>4}  {FREQS[i]:7.2f} Hz   {keybank[i]:.4f}")

print("\nC3 .. C5:")
for i in np.where((MIDI >= 48) & (MIDI <= 72))[0]:
    print(f"{name(MIDI[i]):>4} {FREQS[i]:7.1f} |{'#' * int(keybank[i] * 300)}")
