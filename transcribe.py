"""Piano transcription from scratch. One layer at a time.

Layer 1: synthesize piano-ish audio and its ground-truth labels.
"""
import numpy as np
from scipy.io import wavfile

SR = 16000  # samples/sec
LOW, HIGH = 21, 108  # MIDI range of an 88-key piano (A0..C8)
N_KEYS = HIGH - LOW + 1


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
