"""Layer 1: write a C-major chord to a .wav using only the stdlib.

A note is a sine wave at some frequency. A chord is those sines added together.
That's it -- no library does anything smarter than this.
"""
import math, struct
from wave import Wave_write

RATE = 44100  # samples per second
SECONDS = 2.0
NOTES = {"C4": 261.63, "E4": 329.63, "G4": 392.00}

n = int(RATE * SECONDS)
samples = []
for i in range(n):
    t = i / RATE  # time in seconds
    value = sum(math.sin(2 * math.pi * f * t) for f in NOTES.values())
    samples.append(value / len(NOTES))  # average, so we stay in [-1, 1]

# float [-1,1] -> signed 16-bit int, which is what a .wav actually stores
pcm = b"".join(struct.pack("<h", int(s * 32767)) for s in samples)

with Wave_write("chord.wav") as w:
    w.setnchannels(1)  # mono
    w.setsampwidth(2)  # 2 bytes = 16-bit
    w.setframerate(RATE)
    w.writeframes(pcm)

print(f"wrote chord.wav: {NOTES}")
print(f"{n} samples, {len(pcm)} bytes")
print("first 8 samples:", [round(s, 4) for s in samples[:8]])
