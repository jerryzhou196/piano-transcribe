"""Aside: fine bins != fine resolution.

Zero-padding interpolates the spectrum onto an arbitrarily fine grid --
it is the 'continuous transform' you're imagining. It does not help.
Only more SECONDS of audio helps.
"""
import numpy as np

RATE = 44100
A0, As0 = 27.50, 29.14                      # two adjacent bottom keys

def spectrum(seconds, grid):
    t = np.arange(int(RATE * seconds)) / RATE
    x = (np.sin(2 * np.pi * A0 * t) + np.sin(2 * np.pi * As0 * t)) / 2
    spec = np.abs(np.fft.rfft(x, n=grid)) / len(x)
    return np.fft.rfftfreq(grid, 1 / RATE), spec

def show(title, seconds, grid):
    fr, sp = spectrum(seconds, grid)
    sel = (fr >= 24) & (fr <= 33)
    fr, sp = fr[sel], sp[sel]
    step = max(1, len(fr) // 24)
    print(f"\n{title}")
    print(f"  audio={seconds*1000:.0f}ms  bin spacing={RATE/grid:.3f}Hz  resolution=1/T={1/seconds:.2f}Hz")
    for i in range(0, len(fr), step):
        mark = " *" if abs(fr[i]-A0) < 0.3 or abs(fr[i]-As0) < 0.3 else ""
        print(f"  {fr[i]:6.2f} |{'#' * int(sp[i] * 90):<40}{mark}")

show("93ms of audio, normal grid",          4096/RATE, 4096)
show("93ms of audio, 64x FINER grid",       4096/RATE, 262144)
show("2000ms of audio, same fine grid",     2.0,       262144)
