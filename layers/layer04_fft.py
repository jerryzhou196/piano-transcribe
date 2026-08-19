"""Layer 4: numpy.fft -- Layer 3's correlator run at every bin simultaneously."""
import struct, wave
import numpy as np

with wave.open("chord.wav", "rb") as w:
    rate, n = w.getframerate(), w.getnframes()
    x = np.array(struct.unpack(f"<{n}h", w.readframes(n))) / 32767

N = 4096
chunk = x[:N]

spec = np.abs(np.fft.rfft(chunk)) / N     # magnitude per bin
freqs = np.fft.rfftfreq(N, 1 / rate)      # the frequency each bin stands for

print(f"{N} samples -> {len(spec)} bins, spaced {freqs[1]:.2f} Hz apart")
print(f"bin 0 = {freqs[0]:.0f} Hz ... bin {len(spec)-1} = {freqs[-1]:.0f} Hz (Nyquist)\n")

top = np.argsort(spec)[::-1][:6]
print("6 loudest bins:")
for b in sorted(top):
    print(f"  bin {b:4d} = {freqs[b]:7.1f} Hz  magnitude {spec[b]:.4f}")

lo, hi = 180, 460
print(f"\nspectrum, {lo}-{hi} Hz:")
for b in range(int(lo / freqs[1]), int(hi / freqs[1])):
    print(f"{freqs[b]:6.1f} |{'#' * int(spec[b] * 300)}")
