# sound-design — Sound design

Sound is a timeline-level asset: manage the frame-pinned SFX table centrally; do not embed audio in scene components.
For new productions and replacement sounds, search and download from **Freesound**; see [sfx-sourcing.md](sfx-sourcing.md) for the procedure.
The repository no longer maintains a shared SFX library; historical template audio is retained only for unchanged previews and regression verification.

## 1. Method

1. During storyboarding, note the action, material, duration and timbre; pin SFX precisely after the visual timeline is locked.
   For beat-synced videos with user-specified BGM, first analyze the music using [music-beat-sync.md](music-beat-sync.md), then storyboard.
2. Lay down the BGM first to establish the energy structure, then pin actions unique to the visuals. Strong drum hits already provide a beat; do not add a duplicate impact on every beat.
3. Choose SFX for the type of video and the actual sound source: whoosh (camera movement), impact (landing), riser (buildup),
   sparkle (light effects), transition (scene transitions); give distinctive actions their own real-world Foley.
4. Audition candidates in the context of the finished video. Download counts, ratings, descriptions and waveforms are screening evidence, not grounds for saying you have listened to a sound.
5. Download into the current project's `public/audio/sfx/`, retaining `audio-manifest.json` and
   `FREESOUND-CREDITS.md` with the files; Remotion reads only these fixed local files and does not search online for sounds during rendering.
6. Derive the sound schedule from `SHOTS` and reuse it in the workbench; after timeline changes, recheck each entry, then accept against
   section A of [final-review.md](final-review.md).

## 2. BGM selection and mixing

The Freesound route handles SFX. For BGM, retain the user's specified music or the alternatives in `assets/audio/bgm/`;
see `assets/audio/ATTRIBUTION.md` for licensing. Do not apply an SFX license to the music.

- Music energy should match the video's structure. For product promos, try an electronic bed with clear beats first; the user's tonal requirements take precedence.
  Audition candidate tracks under the finished video rather than choosing music that clashes with the product simply because it is cheerful or pleasant.
- Set volume from actual measurements of the material. The template's BGM at 0.34 and SFX at 0.2–0.6 are historical references only;
  `volume` is a multiplier, not a target loudness. After combining tracks, check for clipping and whether narration/SFX are masked.
- Use `interpolate` for beginning/end fades; duck the music during speech when there is narration.
- Control the BGM `<Audio>` separately with the `bgm` inputProp (default true). For videos with BGM, deliver versions with BGM / without BGM (retaining SFX) from the same
  timeline. For a cross-platform no-BGM render, use
  `--props=props-nobgm.json`, with file contents `{"bgm":false}`.

## 3. Timbre and sound selection

### 3.1 Build search terms from the visuals

The full selection rules and CLI are in [sfx-sourcing.md](sfx-sourcing.md). Define the source, texture,
attack length and tail before searching Freesound; do not search only broad terms such as `click` or `impact`.

| Visual | Example query | Selection focus |
|---|---|---|
| Card fly-in / camera movement | `short soft whoosh` | Attack-peak position; no overlong tail |
| Paper-card slide-in / page turn | `dry paper slide` / `single page turn` | Real paper sound; a single action |
| Switch / light tap | `mechanical switch click` | Brief physical texture; avoid notification tones |
| Wordmark landing | `short cinematic impact` | Sense of weight; low frequencies must not mask the BGM |
| Typing | `computer keyboard typing` | Rhythmic density, passage length and background noise |
| Assembly and lingering finish | `cinematic riser` / `subtle shimmer` | Whether the crescendo reaches the landing; whether the tail is natural |

### 3.2 Check repeated-action candidates for duplicates first

Two names or two Freesound IDs may represent the same sound. Use the manifest's SHA-256 to identify identical files,
then audition them to confirm timbral differences; different encodings of the same recording may have different hashes. Do not treat renamed copies of the same sound
as two alternating samples. Do not download an entire library; take only the candidates needed for the current action.

### 3.3 Assess the timbre of each UI action separately

S1 prohibits a game-like synthetic notification texture, not clicking as an action. Real switch, shutter, glass and paper Foley can work;
`confirmation tone`, `bleep` and `notification` often indicate synthetic feedback and should not be selected merely because a query matches.
They can be used when the video deliberately depicts a system notification; explain the narrative reason in the design record.

A recording description with a clear sound source and equipment is a useful clue; `made with my mouth` or `built-in mic`
may not suit a clean product video. Equipment names cannot guarantee quality; still audition the sound within the video.

## 4. Alignment techniques

### 4.1 Frame pinning, duration and volume

- Keep the central registry as `{ from, src, volume }[]`, optionally extended with `durationInFrames`;
  annotate each entry with its action and mount it through `<Sequence>` in the rendering layer. Derive workbench tracks from the same table.
- Use the downloaded file's `analysis`; do not treat the source-file duration/sample rate listed on the web page as measurements of the preview file.
  `get` analyzes automatically; after processing or replacing a file, run `analyze` again and update the manifest and hashes.
- Give action sounds an explicit playback window, especially keyboard, ambient and mechanical samples >5s.
  Crop the Sequence to the action duration; let background noise cover its corresponding passage. An impact's natural reverb may extend beyond the landing; avoid a hard cut.
- For quiet material with peaks below -12dB, first consider a cleaner candidate or preprocessing followed by a new analysis.
  Gain >1 can be used when necessary, but preview and render behavior may differ; prevent clipping using actual measurements of the finished render.
- The tools report the peak of the RMS energy envelope in 10ms windows, sample peak and overall RMS, **not LUFS or true peak**.
  For repeated hits or crescendos, choose the meaningful landing manually; do not mechanically use the file's largest peak as the landing for every action.

### 4.2 Avoid a machine-gun effect in rapid repeats

Alternate two samples, reduce volume in steps (for example, 0.40→0.25), and let the spacing follow the animation's acceleration.
When hits become too dense to hear individually, consolidate them into a swoosh or fade them out; do not let multiple long tails pile up into noise.

### 4.3 riser→impact→sparkle: a shot-closing phrase

Start a riser during the assembly buildup, pin an impact to the main object's landing, and add a sparkle to the lingering finish. Set the spacing
between them from the shot's actual landings and select three matching sources from Freesound; do not reuse template filenames or absolute frame numbers.
Whether to use this phrase depends on the storyboard; do not force the same sound onto every ending.

### 4.4 Recheck after visual revisions

When a shot's duration, order or action peak changes, recheck its sound window and all subsequent pins;
changing only the visuals without checking sound causes misalignment. Select material early if useful, but do precise frame pinning after the timeline is locked.

### 4.5 Pin frames relative to the shot start

Write `SHOTS.<shot>.from + offset`, or `beatF(n)` for beat-synced videos; do not use bare absolute frame numbers in new projects.
SFX then follows changes to the shot's start, but changes to the action inside the shot still require rechecking.

### 4.6 Compensate for two offsets in audiovisual alignment (hard rule)

The design intention is for the source sound's peak to land on the target beat frame. Two offsets stand between that intention and the finished render,
and they add up when neither is compensated. The heaviest hit measured in this repository arrived 0.27s late, perceptibly out of sync;
in a beat-synced video, a difference of 2–3 frames can be enough for viewers to miss that a motion follows the drums,
reading an otherwise sensible beat-synced effect as unexplained shaking (S5 case). Use this single formula (calculate in floating point and round only at the final step):

```
Sequence.from = target peak frame − source peak-lag frames − output audio-offset frames
```

**Offset one: final output audio offset (measure for each rendering pipeline).**
The finished render's entire audio track has a fixed lag relative to the video. The root cause lies in the **output encoding/muxing
chain**, not the behavior of `<Audio>` or `Sequence.from`: AAC encoders have
encoder priming (warm-up samples padded at the start); at 48kHz, a typical value is 2048 samples
= 1.28f@30fps. This repository's AiflPromo measurements found a click lag of 2032 samples and
an impact lag of 2066 samples (≈1.27–1.29f), matching the priming signature. The rendered
artifact's (aifl-ref.mp4) audio edit list (elst media time=0) did not declare trimming of this
padding, so decoding exposes a real offset. Remotion officially tracks the same family of issue:
remotion-dev/remotion#7099.

- **Record by pipeline, not by video**: the offset depends on four factors, Remotion version + audio codec +
  sample rate + container. Save the measurement with all four; reuse it when all four stay unchanged,
  but remeasure if any changes. Priming magnitude differs by encoder (ffmpeg's built-in
  aac ≈1024, fdk-aac 2048, Apple ≈2112 samples); do not assume a constant.
- A **4f** offset (≈133ms/6400 samples) was measured in the promo-ink era, far beyond what
  priming can explain, and its root cause was not verified. Retain it only as a warning that
  old constants cannot be carried across pipelines, not as a statement of mechanism.

Measurement method (after rendering; one accurate measurement applies across the same pipeline):

```bash
ffmpeg -i out/promo.mp4 -vn -acodec pcm_s16le /tmp/render-audio.wav
```

Perform normalized cross-correlation of the **original files** for 2–3 sharp SFX against the rendered audio track (numpy
`np.correlate` is sufficient). Subtract the designed frame position from the peak position to obtain the offset; consider the measurement accurate
only when multiple probes have consistent residuals. A single point may instead reflect the source sound's own peak lag.

**Offset two: the source sound's own peak lag (measure each file).**
Many sounds do not peak at the start of the file (a rising attack or a leading breath), so aligning the file's start makes them
arrive late. Measured examples: brush-write 2f, paper-slide 10f, ink-char as much as 24f.
Locate the peak using the audio energy envelope, and record it with max_volume when adding a new sound
(see 4.1; the same principle as music-beat-sync §4, “align material to its internal peak, not the file's start”).

Rendering-layer implementation: keep the SFX table's `{ from, src, volume }` schema from §4.1 unchanged;
separate the three components in the expression calculating `from` (retain the full audit chain; never hand-edit frame numbers entry by entry):

```tsx
// Measured for this pipeline: Remotion 4.x + AAC 48kHz mp4, 2026-08-23, click/impact dual-probe cross-correlation
const OUTPUT_AUDIO_OFFSET_F = 1.28;
const PEAK_F: Record<string, number> = { 'impact-deep-whoosh.mp3': 2 /* measured per file */ };
const sfxFrom = (targetPeakF: number, src: string) =>
  Math.max(0, Math.round(targetPeakF - (PEAK_F[src] ?? 0) - OUTPUT_AUDIO_OFFSET_F));
// Table entry: { from: sfxFrom(SHOTS.outro.from + 35, 'impact-deep-whoosh.mp3'), src: …, volume: 0.55 }
```

Note two boundaries:
- **Do not add the offset to durationInFrames**: moving the whole window earlier brings its start and end back into
  perceptual alignment together. Lengthening the window of a cropped effect (a long sample explicitly cut with durationInFrames)
  plays extra content that should have been removed.
- The `Math.max(0, …)` fallback means pins within roughly 2f of the beginning cannot receive full compensation;
  record the residual in the acceptance table. Avoid designing a strong opening hit in the first 2 frames where possible.

The same applies to BGM, but record it in a different place: leave the source-music grid constant `SOURCE_BEAT0` at its
true analyzed value and use a separate output-offset constant in the `beatT` conversion; see music-beat-sync
§5b. Both use the same cross-correlation measurement method.

Acceptance: rerender after compensation and rerun cross-correlation for 2–3 probes; residuals ≤0.5f pass.
