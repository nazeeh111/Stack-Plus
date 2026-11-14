# music-beat-sync — BGM rhythm analysis and beat synchronization

With strongly rhythmic BGM, **all transitions and key motion must land on beats**. This document gives a reproducible process from receiving a track to finished-video cut-point error ≤3 frames. In an observed 70s, 18-shot promo with strong drums at 131.97 BPM, post-render checks found all cut-point errors ≤2.2f; the perceptual threshold is about 3f.

## Contents

- When to use it
- Measuring the beat grid
- Drum classification and energy structure
- Grid acceptance and outputs
- Scheduling the timeline by beats
- Post-render verification
- Tool notes

## 0. When to use it

At stage 0, first check whether the user has specified music.
- Already selected → follow this document: analyze rhythm first, then anchor every storyboard cut/motion to beat indices.
- Not selected → choose BGM at stage 6 (pipeline.md); schedule motion by content pacing for now without forcing beat sync.

**Hard rule: music first.** Do not storyboard before the grid passes acceptance. When duration does not fit, change timing parameters rather than deleting or rewriting user copy. Record times as floating-point seconds throughout analysis; **convert to frames only at the final Remotion step**. Early rounding compounds errors through the pipeline.

## 1. Measure the beat grid; do not trust beat_track's tempo scalar

Run a one-off script with `uv run --with librosa --with scipy --python 3.11`:

```python
import numpy as np, librosa

y, sr = librosa.load("bgm.mp3", sr=None, mono=True)
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, tightness=400, units="time")

# Critical step: least-squares fit an equally spaced grid to the beat sequence
# to obtain the true BPM and phase.
# beat_track's tempo scalar may be wrong by 2%+ (observed 129.2 vs true 131.97),
# although its beat times are good: fit t_i = t0 + i*T to the entire sequence.
i = np.arange(len(beats))
A = np.vstack([i, np.ones_like(i)]).T
(T, t0), *_ = np.linalg.lstsq(A, beats, rcond=None)
bpm = 60.0 / T
residual = beats - (t0 + i * T)
print(f"BPM={bpm:.2f}  t0={t0:.4f}s  T={T:.5f}s  residual±{np.abs(residual).max()*1000:.0f}ms")
```

Acceptance: residuals ≤ ±15ms, within half a frame, indicate machine-timed drums and a trustworthy grid. Larger residuals suggest tempo-changing sections that need separate fits.

**Always check half/double-time ambiguity**: beat detection often jumps between 2x/0.5x, for example reporting 70 BPM as 140. Decide from the drum data in the next section, not listening alone. On the correct grid, kicks should mainly land on integer beats. If half fall on beats and half on half-beats, the grid is probably twice too fast. Score the 0.5x/1x/2x candidates against §3's metrics and choose the highest coverage.

**Separate a drum stem first for complex tracks**: dense vocals/bass can bury drum attacks, causing both beat_track and onset detection to drift. A lightweight option is the percussive component from `librosa.effects.hpss`; a heavier option is a Demucs drum stem (§6). Then detect all drum events on that stem, not the full mix.

## 2. Drum classification and energy structure: what goes on which beat

### 2a. Three-class transient detection

Different drum parts drive different motion types. Measure each frequency band on the drum stem or HPSS percussive component:

| Class | Frequency band | Motion it drives |
|------|------|-----------|
| kick | 40–160 Hz | Impact / slam / abrupt shrink: the beat where the image is struck |
| snare | 150–500 Hz body + 1–3 kHz attack, requiring both | Replacement / flash cut / composition change: a change-of-subject beat |
| hihat | 6–14 kHz | Micro-motion density: dense hihats allow denser micro-motion; sparse sections require restraint |

```python
from scipy.signal import butter, sosfilt
def band_env(y, sr, lo, hi):
    sos = butter(4, [lo, hi], btype="band", fs=sr, output="sos")
    env = librosa.onset.onset_strength(y=sosfilt(sos, y), sr=sr)
    return env, librosa.times_like(env, sr=sr)

kick_env, times = band_env(y, sr, 40, 160)
# List envelope energy at each integer beat; sort to find the strongest hits:
for n in range(int((times[-1]-t0)/T)):
    t = t0 + n*T
    e = kick_env[np.argmin(np.abs(times - t))]
    # Record (beat index n, energy e); take the top few as major-slam candidates.
```

Archive hits as a list `{t seconds, s strength, k class}` for selection by class during storyboarding.

**The hit table is a candidate pool, not a trigger.** Every detected kick does not require a visual impact. Strong-drum tracks such as tech house have a kick almost every beat; striking the frame every beat creates “镜头随节奏抖动” (“the camera shakes with the rhythm”), an actual user complaint referenced in aesthetic-rules R4. The kick→impact mapping only selects §2b's strongest hits, 2–3 per video. Other kicks provide **timing** for cuts/element motion, not whole-frame amplitude.

### 2b. RMS energy curve and structure table

Use `librosa.feature.rms` for the complete energy curve, with drum density to identify section boundaries. Add two outputs to the design spec:

- **Music-structure table**: beat indices where full energy starts and where breakdowns/silence occur. Schedule the storyboard energy curve accordingly. A breakdown naturally suits brand breathing space; high-energy shots may run multiple motion layers, while low-energy sections reduce to 1–2 layers.
- **Strongest-hit beat list**: anchor the video's 2–3 biggest slams, for opening/climax/ending, to these beats.

**Observed pitfall**: the biggest slam was pinned at b52.5, between beats, while the strongest kick was on integer beat b52, causing +5.75f post-render error. Strong-drum accents are almost always on integer beats; half-beat anchors require envelope evidence, not listening alone.

## 3. Grid acceptance and outputs: accept before storyboarding

Align each candidate grid, including 0.5x/1x/2x, to the nearest actual drum transients and compute four metrics:

| Metric | Meaning | Threshold |
|------|------|------|
| match | Fraction of grid beats matching actual transients | ≥98% |
| mean_abs_ms | Mean absolute alignment error | <10ms |
| drift | Slope of a linear regression of residual against time | Accumulated whole-track drift <5ms |
| First-beat validity | Grid beat 0 falls on a real musical attack | Required |

Select the winning grid by scores and archive **all candidates and the selection rationale**. If uncertain, synthesize a click track for each candidate, overlay it on the original and listen; the metrics still decide the result, not listening alone.

Keep analysis outputs with the project as the audit chain for every cut:

```text
analysis/
  beat_data.json    # bpm, t0, T, beats[], hits[{t,s,k}], rms[], sections[]
  grid_drift.json   # Candidate grids' match/error/drift and winning rationale
  click_*.wav       # Optional candidate click tracks for listening checks
```

Times in `beat_data.json` always remain floating-point seconds, never rounded early. Downstream work depends only on the field names `bpm / beats / hits / rms / sections`.

## 4. Write the timeline in beats, not frame numbers

Make the grid constants in the Remotion project; express every shot boundary/motion keyframe with `beatF()`:

```ts
export const FPS = 30;
export const SOURCE_BEAT0 = 0.2244;  // Source-music analysis t0 in seconds, matching beat_data.json
export const BEAT_INT = 0.45465;     // T in seconds
export const OUTPUT_AUDIO_OFFSET_SEC = 0; // Measured output-audio offset if post-render checks confirm one (§5b)
export const beatT = (n: number) =>
  SOURCE_BEAT0 + OUTPUT_AUDIO_OFFSET_SEC + n * BEAT_INT;           // Beat → seconds
export const beatF = (n: number) => Math.round(beatT(n) * FPS);    // Beat → frames

export const SHOTS = {
  s0_open:  { from: 0,        to: beatF(8) },
  s1_slam:  { from: beatF(8), to: beatF(16) },
  // …Every shot boundary is beatF(integer beat); internal motion uses local beats:
};
export const localBeat = (shot: {from: number}, n: number) => beatF(n) - shot.from;
```

Changing track/section then requires changing two constants to reschedule the whole video. The SFX table also uses `beatF(n)`, sharing the visual timeline's source of truth to prevent misalignment. Keep source analysis and render offset separate: `SOURCE_BEAT0` is immutable audit truth; output offset belongs only in `OUTPUT_AUDIO_OFFSET_SEC`.

**Anchor rules: grid versus actual transients**:

- Dense regular cuts, every beat or every two beats → winning grid's `beatF(n)`.
- Sparse accents/isolated freezes → **actual transients**, not interpolated grid points. Small drift in sparse sections becomes perceptible on a single accent.
- Ending freeze → last actual transient plus RMS silence confirmation, avoiding a reverb-tail anchor.
- Align video/SFX by **internal peaks**, not file starts: `asset start = target beat time − (peak time − trim offset)`. Locate peaks with an audio energy envelope or FFmpeg frame differences.

Design rules:
- Shot lengths use beats, typically 4/8 beats per shot. Accelerating sections can step in half/quarter beats, for example the converging sequence CUT_BEATS = [48, 49.5, 50.5, 51, 51.25].
- Stepwise shots, such as list items or mosaic cells, map directly to beat indices.
- With dense BGM drums, use SFX sparingly: pin only visually unique actions and reserve major slams for 2–3 moments, leaving other accents to BGM drums.
- **Whole-frame impacts have a hard cap**: every instantaneous impact on the whole frame/camera, including scale pumping, shake, flash frames and negative frames, counts. Limit to ≤3 per video, corresponding one-to-one with §2b's strongest-hit list, with ≥16 beats between adjacent uses. Repeated beat-pumping may last ≤4 beats per use and occur ≤1 time per video, followed by sufficient hold; each card's specified values are minimums. Count **one use of a technique**: one card application consumes one slot. Do not count each internal flash of a repeated-flash/multi-cut card separately; the card's own parameter table/repetition limits govern its internal structure.
- **Beat-synced motion defaults to protagonist element layers**, such as cards/titles/numbers. Whole-frame/camera layers do not move on every beat by default. “One action per beat” means content progression, such as items/cells, not a whole-image amplitude pulse.
- Structural motion (deformation/camera/pose) uses continuous frame functions; impact events (appearance/replacement/flash/abrupt shrink) switch at their selected frame. Layers hitting on the same frame create an accent. Deliberate staggering is only 1–2 frames, with explicit design intent, never accidental rounding misalignment.

## 5. Post-render verification: required closed loop

### 5a. Report two kinds of error separately

- **Audio ground-truth error**: designed cut time in seconds versus real transient time, testing the analysis pipeline. Require mean <5ms, all within ±33ms, and 90% within ±15ms.
- **Visual quantization error**: rounding when seconds convert to the nearest renderable frame, testing whether the frame rate is sufficient. This is the `beatF()` rounding error; record it for every anchor.

Nearest-frame error bounds depend on FPS: 30fps ±16.7ms, 60fps ±8.3ms, 120fps ±4.2ms. **Do not claim <5ms visual precision for 30fps delivery.** If the quantization report exceeds tolerance, increase frame rate rather than changing audio analysis.

### 5b. Extract rendered audio and measure again

```bash
ffmpeg -i out/promo.mp4 -vn -acodec pcm_s16le /tmp/render-audio.wav
```

Repeat step 1's grid fitting on the rendered track. Measure BGM from the video, not the source, to include encoding/alignment offsets. Compare each **designed cut frame against the nearest measured beat frame** and output an error table.

| Judgment | Error |
|------|------|
| Pass | ≤3f, the perceptual threshold |
| Ideal | ≤1.5f |
| Must fix | Any cut >3f |

Return failing anchors to step 4, adjusting beat indices or frame offsets, then render/measure again until every row passes.

**For a uniform directional offset, check output-audio delay before editing individual anchors.** If every cut has the same +N-frame error, the source is almost always render-output audio offset, such as AAC encoder priming/encoding/muxing. A typical 48kHz offset is ≈1.28f; see sound-design §4.6 for mechanism/measurement. Measure it by normalized cross-correlation between source BGM and rendered audio. **Keep output offset in its own constant, never write it back to source analysis.** `beat_data.json`'s t0 is the source-music analysis truth/audit baseline; mixing render offsets into it double-compensates after a codec change or reanalysis. Track them separately:

```ts
export const SOURCE_BEAT0 = 0.2244;        // Source-music analysis t0, matching beat_data.json; never mix in render offset
export const OUTPUT_AUDIO_OFFSET_SEC = 0.0427; // Output-track offset measured for the render pipeline (sound-design §4.6)
export const beatT = (n: number) => SOURCE_BEAT0 + OUTPUT_AUDIO_OFFSET_SEC + n * BEAT_INT;
```

One `beatT` correction realigns all cuts. **Do not manually change beat indices anchor by anchor.** SFX compensation uses the same constant through sound-design §4.6. The damage is not merely inaccuracy: an impact 2–3 frames off no longer sounds drum-driven, so otherwise reasonable beat motion reads as unexplained shaking.

## 6. Tool notes

- librosa is not in system Python: `uv run --with librosa --with scipy --python 3.11 script.py`.
- Vocal-only/complex arrangements can make beat_track drift. First separate percussive content with `librosa.effects.hpss`. If still unclear, separate drums with Demucs: `uvx --from demucs demucs --two-stems=drums -n htdemucs bgm.mp3 -o analysis/`, then run all of §1/§2 on `drums.wav`.
- For uncertain BPM, cross-check methods: madmom's RNN+DBN and Essentia's RhythmExtractor2013 provide second/third votes alongside librosa. When they disagree, return to §3 and decide by transient coverage rather than guessing.
- For changing tempo, such as DJ transitions/accelerando, use a local librosa tempogram with an approximately 5s window to identify changes, then fit energy sections separately, each with its own t0/T.
