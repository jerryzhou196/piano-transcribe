"""Layer 2: read chord.wav back into numbers and draw it.

Goal: convince yourself the notes are genuinely unreadable in the time domain.
"""
import struct, wave

with wave.open("chord.wav", "rb") as w:
    rate = w.getframerate()
    n = w.getnframes()
    raw = w.readframes(n)

# bytes -> ints -> floats in [-1, 1]
ints = struct.unpack(f"<{n}h", raw)
samples = [v / 32767 for v in ints]

print(f"rate={rate} Hz  samples={n}  duration={n/rate:.1f}s")
print("samples 0..9:", [round(s, 3) for s in samples[:10]])

# ASCII plot of the first 10 ms (441 samples), 60 columns wide
WIDTH, MS = 60, 10
window = samples[: int(rate * MS / 1000)]
step = len(window) / WIDTH
print(f"\nfirst {MS} ms of the waveform:")
for row in range(9, -1, -1):                   # 10 rows, +1.0 down to -1.0
    hi, lo = (row - 4.5) / 5 + 0.1, (row - 4.5) / 5 - 0.1
    line = "".join(
        "#" if lo <= window[int(c * step)] < hi else " " for c in range(WIDTH)
    )
    print(f"{(row-4.5)/5:+.1f} |{line}")
