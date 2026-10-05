"""Original deterministic ambient synthesis. No samples, third-party recordings or voice."""
from pathlib import Path
import numpy as np
import wave

out = Path(__file__).resolve().parents[2] / '.local/tour/evidence-bed.wav'
out.parent.mkdir(parents=True, exist_ok=True)
sr = 48000
t = np.arange(sr * 22, dtype=np.float64) / sr
sound = np.zeros(t.shape)
chords = [(146.8324, 220., 261.6256), (130.8128, 195.9977, 246.9417),
          (164.8138, 220., 293.6648), (146.8324, 220., 293.6648)]
for index, notes in enumerate(chords):
    start = index * 5.5
    envelope = np.clip((t - start + .6) / .8, 0, 1) * np.clip((start + 6.1 - t) / .8, 0, 1)
    for voice, frequency in enumerate(notes):
        phase = 2 * np.pi * frequency * t + voice * .37
        sound += envelope * .017 * (np.sin(phase) + .16 * np.sin(2 * phase)) * (1 + .07 * np.sin(2 * np.pi * .19 * t))
for when, frequency in [(2.2, 587.33), (10.3, 880.), (20., 440.)]:
    dt = t - when
    envelope = np.where(dt >= 0, np.exp(-np.maximum(dt, 0) * 9) * np.clip(dt / .012, 0, 1), 0)
    sound += .032 * envelope * np.sin(2 * np.pi * frequency * dt)
sound *= np.clip(t / .5, 0, 1) * np.clip((22 - t) / .9, 0, 1)
right = .92 * sound + .08 * np.roll(sound, int(sr * .061))
stereo = np.stack((sound, right), axis=1)
assert float(np.max(np.abs(stereo))) < .15
with wave.open(str(out), 'wb') as wav:
    wav.setnchannels(2)
    wav.setsampwidth(2)
    wav.setframerate(sr)
    wav.writeframes((stereo * 32767).astype('<i2').tobytes())
print(out)
