"""Piano transcription from scratch. One layer at a time.

Layer 1: synthesize piano-ish audio and its ground-truth labels.
Layer 2: turn samples into a spectrum - energy per frequency.
Layer 3: learn spectrum -> which keys are down.
"""
import numpy as np
from scipy.io import wavfile
from sklearn.linear_model import Ridge

SR = 16000  # samples/sec
LOW, HIGH = 21, 108  # MIDI range of an 88-key piano (A0..C8)
N_KEYS = HIGH - LOW + 1
FRAME = 2048  # samples per analysis window = 128ms, ~7.8 Hz per frequency bin


def midi_to_hz(m):
    """MIDI note number -> frequency. 69 = A4 = 440 Hz, 12 steps per octave."""
    return 440.0 * 2.0 ** ((m - 69) / 12)


def pluck(midi, dur=0.5):
    """One note: fundamental + 3 harmonics at 1/k amplitude, struck-string decay."""
    t = np.arange(int(dur * SR)) / SR
    f = midi_to_hz(midi)
    wave = sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, 5))
    return wave * np.exp(-3 * t)
    # ponytail: pure harmonics. Real strings are inharmonic (upper partials run sharp);
    # add a stiffness term if the model turns out to have it too easy.


def render(events, dur=0.5):
    """events: list of (midi, ...) tuples, one chord per slot.

    Returns (audio, labels) where labels[i, k] == 1 means key LOW+k is down in slot i.
    """
    audio, labels = [], np.zeros((len(events), N_KEYS))
    for i, chord in enumerate(events):
        mix = sum(pluck(m, dur) for m in chord)
        audio.append(mix / max(len(chord), 1))  # volumne normalization
        for m in chord:
            labels[i, m - LOW] = 1
    return np.concatenate(audio), labels


BIN_HZ = np.fft.rfftfreq(FRAME, 1 / SR)  # what frequency each FFT bin means


def spectrum(frame):
    """FRAME samples -> magnitude at each frequency bin. The whole trick."""
    windowed = frame * np.hanning(FRAME)  # taper the edges or the FFT smears
    return np.abs(np.fft.rfft(windowed))


def featurize(audio, n_slots, dur=0.5):
    """One spectrum per slot, taken from the loud attack at the slot's start."""
    step = int(dur * SR)
    return np.stack([spectrum(audio[i * step : i * step + FRAME]) for i in range(n_slots)])


def top_peaks(spec, n=5):
    """The n loudest bins, as (frequency, magnitude) pairs."""
    idx = np.argsort(spec)[-n:][::-1]
    return [(BIN_HZ[i], spec[i]) for i in idx]


TRAIN_LOW, TRAIN_HIGH = 36, 84  # C2..C6
# ponytail: middle of the keyboard only. The extremes need a finer FRAME (low notes
# blur together at 7.8 Hz/bin) and less aliasing headroom - widen once the middle works.


def dataset(n, seed, dur=0.5):
    """n slots of 1-4 random simultaneous notes -> (log-spectra, labels)."""
    rng = np.random.default_rng(seed)
    keys = np.arange(TRAIN_LOW, TRAIN_HIGH + 1)
    events = [tuple(rng.choice(keys, rng.integers(1, 5), replace=False)) for _ in range(n)]
    audio, y = render(events, dur)
    return np.log1p(featurize(audio, n, dur)), y
    # ponytail: log1p compresses the huge dynamic range between fundamental and
    # harmonics, so quiet partials still move the weights. Raw magnitudes work worse.


def fit(X, y):
    """One linear map from 1025 bins to 88 keys. No hidden layer, no epochs."""
    return Ridge(alpha=1.0).fit(X, y)
    # ponytail: linear is enough because a key's harmonics land in fixed bins - the
    # model just learns "these bins hot -> this key". Go neural when real recordings
    # (varying velocity, pedal, overlapping onsets) break that assumption.


def predict(model, X, thresh=0.5):
    """Ridge outputs a score per key; anything past thresh counts as pressed."""
    return model.predict(X) > thresh


def score(pred, y):
    """Note-level precision/recall plus how often the whole chord is exactly right."""
    hit = (pred & (y > 0)).sum()
    return dict(
        precision=hit / max(pred.sum(), 1),
        recall=hit / y.sum(),
        exact=(pred == (y > 0)).all(axis=1).mean(),
    )


if __name__ == "__main__":
    # C major scale, then a C major chord, then C4+C5 (the ambiguous case)
    events = [(60,), (62,), (64,), (65,), (67,), (60, 64, 67), (60, 72)]
    audio, labels = render(events)

    assert audio.shape == (len(events) * int(0.5 * SR),)
    assert labels.sum() == sum(len(e) for e in events)

    print(f"audio: {audio.shape[0]} samples = {audio.shape[0]/SR:.1f}s @ {SR} Hz")
    print(f"labels: {labels.shape}  (one row per slot, 88 keys wide)\n")
    print("raw samples (what the computer actually receives):")
    print(" ", np.round(audio[:8], 3), "...\n")
    for e, row in zip(events, labels):
        keys = np.flatnonzero(row) + LOW
        print(
            f"  slot: midi {str(e):<14} -> {int(row.sum())} key(s) on at index {keys}"
        )
        print(f"        {' '.join(f'{midi_to_hz(m):.1f}Hz' for m in e)}")

    wavfile.write("demo.wav", SR, (audio * 0.3 * 32767).astype(np.int16))
    print("\nwrote demo.wav - play it, it should sound like a cheap keyboard")

    # --- layer 2 ---
    X = featurize(audio, len(events))
    print(f"\nspectra: {X.shape}  ({X.shape[1]} frequency bins per slot)\n")

    for slot in (0, 6):
        played = " + ".join(f"midi {m} ({midi_to_hz(m):.0f}Hz)" for m in events[slot])
        print(f"slot {slot}: {played}")
        for hz, mag in top_peaks(X[slot]):
            print(f"    {hz:7.1f} Hz  {'#' * int(30 * mag / X[slot].max())}")
        print()

    # --- layer 3 ---
    Xtr, ytr = dataset(600, seed=0)
    Xte, yte = dataset(200, seed=1)  # different seed = chords it has never heard
    model = fit(Xtr, ytr)
    s = score(predict(model, Xte), yte)
    print(f"held-out: precision {s['precision']:.3f}  recall {s['recall']:.3f}  "
          f"exact chord {s['exact']:.1%}")
    assert s["exact"] > 0.8, s

    # and on the hand-written events from layer 1
    for e, row in zip(events, predict(model, np.log1p(X))):
        got = tuple((np.flatnonzero(row) + LOW).tolist())
        print(f"  played {str(e):<14} -> heard {str(got):<14}{'' if got == tuple(sorted(e)) else '<- wrong'}")
