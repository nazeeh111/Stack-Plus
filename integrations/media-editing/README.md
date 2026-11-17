# Video editing and clipping

Use existing editing foundations with explicit readiness. A method being installed
does not mean its renderer, transcription model or native editor is commissioned.
The runtime index owns each machine's absolute command and observed checks.

## Choose the working route

| Work | Foundation | Verified scope and prerequisites |
| --- | --- | --- |
| Frame/sample cuts, export, captions, transitions, loudness | Separately recorded full FFmpeg/FFprobe | Actual synthetic cuts, full decode, pixel/sample oracles, caption timing and loudness checks passed on FFmpeg 7.1/FFprobe 8.1.2. This is a different build from P230. |
| Minimal local cue fixture encoding/inspection | `nstack run P230 media -- ffmpeg ...` / `ffprobe ...` | Pinned FFV1/PCM/Matroska source build. Its codec/filter selection is intentionally narrow; do not assume broad editing support. |
| Speech-heavy first cuts and editable NLE export | `auto-editor-audio-video-cuts`, `auto-editor-timeline-conversion` | Methods available; auto-editor runtime is prepared but blocked on this Mac. Native execution/export compatibility is unverified. |
| Native timeline finishing, color and sound | An already installed NLE | DaVinci Resolve 21.1.0 passes signature/notarization assessment. App presence does not prove edition-specific features, scripting permission or timeline import. |
| Native editable timeline and reproducible rendering | Recorded Blender 5.2.1 LTS Video Sequence Editor | Actual paired video/audio strips, trim, save/reopen and boundary-frame renders passed. Exact delivery uses the separately checked post-export audio route below. |
| Product story, shots, pacing and sound | `video-shotcraft` | Read the original production method and relevant sound/beat references. Existing shot cards and examples remain authoritative; source availability does not commission the workbench. |
| Programmatic graphics/compositions | Existing Remotion, HyperFrames, RAEA or Blender route selected for the actual project | Use the project's recorded version/lock and privacy contract. Do not install another framework merely to trim existing footage. |
| Automatic transcription | Recorded source-built Whisper.cpp CPU route | Fresh pinned CPU build transcribed an 11-second public English sample with exact reference words and bounded JSON/SRT word times. Existing model bytes were reused; general language, noise and diarization quality remain task-specific. |

## Auto-editor admission

Installed methods retain upstream source
[5ad05f9](https://github.com/WyattBlue/auto-editor/tree/5ad05f9ee76bc9fe4126bd25463eada082576f88).
The reviewed official runtime candidate is
[31.9.0](https://github.com/WyattBlue/auto-editor/releases/tag/31.9.0), source
1fb5d4939ee2632674d2de117a434622443a0acb,72 commits later. Keep those identities
separate. The release adds timeline imports, transitions, speed ramps and caption
handling; those release notes are source reports, not acceptance here.

The official macOS ARM64 asset matches GitHub's published SHA256
84823f8132a40d1ad072cfaabe432d2a35d1ad022421d7436c51a24bac9e86a5. Its ad-hoc
signature passes byte verification, but native Gatekeeper assessment rejected it.
It was not executed, installed, chmodded or retried through another platform.
No quarantine, signature, trust or permission setting changed. A signed/notarized
upstream artifact or the user's normal native approval is needed before a scoped
trial. Do not present it as functional or add an automatic activation wrapper.

Source builds require Nim 2.2.2+ and nimcrypto 0.7.3 as well as the selected native
media dependencies. Building from source is not a workaround for this rejection.
Core is Unlicense; native libraries, codecs and optional models have their own
notices. No microphone capture follows from an editing request.

## Editing evidence and recovery

The local commissioning fixture used two four-second source clips at 30fps and
48kHz. All120 output frames and 192000 PCM samples matched independent source
oracles after explicit trims. A four-second H264/AAC export with timed captions
fully decoded. A separate 200ms dissolve/audio crossfade had 114 frames and182400
samples. Cut, end, blend and caption frames were visually inspected. Two-pass
loudness processing remeasured -17.97LUFS for a -18LUFS target, with true peak
below the requested ceiling. These are synthetic mechanism checks, not speech
intelligibility or creative-quality acceptance.

An initial combined A/V concat padded 16 audio samples on this Matroska fixture.
The accepted count-based audio and frame-based video concatenation passed complete
oracles. An initial dissolve lacked valid constant-frame-rate metadata; explicit
30fps fixed it. Preserve originals and failed outputs, write a candidate separately,
and replace the accepted render only after decoding and checks succeed. Keep exact
source frame intervals, timebase, audio sample rate and caption offsets with the
editable project. A parsed FCPXML alone does not establish native import/reopen.

For intelligent clipping, select complete semantic units from a reliable
time-aligned transcript, then check surrounding context and words at every cut.
Loudness/silence can propose boundaries; they do not measure narrative importance.
Re-time captions through the edit rather than keeping source timestamps. Review
readability, audio joins and pacing independently on the final export. Synthetic
tone cuts alone cannot establish speech-selection quality. The separate CPU speech
check below supplies bounded actual transcription evidence.

## Local speech transcription

A fresh [Whisper.cpp b4938 source
build](https://github.com/ggml-org/whisper.cpp/tree/371b5a7561823ab2bb32142d2751e35e7534727b)
uses only the CPU backend, with Metal, CoreML, BLAS/Accelerate, CUDA, OpenMP,
KleidiAI, dynamic backends and model-download CURL disabled. The original CLI and
models remain unchanged. A private signed/notarized Kitware CMake 3.31.10 toolchain
was admitted through normal native controls; no global PATH or package changed.
Full source, bundled notices, compiler flags and resulting binary hash are retained
with the machine's runtime receipt. Upstream defaults its development-version
suffix on even at this tag; `1.9.3-dev` alone does not establish a wrong revision.

The existing base.en model matches its official object hash. One upstream public
JFK test sample produced the 22 expected normalized words without error. Fifty-five
checks covered monotonically ordered, source-bounded JSON word segments, SRT
caption times, CPU execution, unchanged model bytes and invalid-input handling.
Word timestamps are approximate model predictions, not forced alignment. The
JSON `offsets` values are milliseconds; compare them with the formatted timestamps
rather than treating them as internal 10ms ticks.

The original CLI can return exit 0 for unreadable audio while producing no
transcript. [whisper_cpu.py](whisper_cpu.py) checks an explicitly admitted CLI/model
hash, bounded mono 16-bit 16kHz WAV input with a complete readable PCM payload,
producer exit and matching fresh
JSON/SRT/TXT timings before accepting a run. It retains stdout/stderr, partials and
a receipt even on failure. Non-regular CLI/model/input paths are refused before
reading their contents; existing run directories are refused before execution.
Twenty-one focused
checks and one fresh actual CPU run passed. An empty transcript is reported
explicitly; use `--expect-speech` when it must fail. Empty output does not prove
the source contained no speech. A missing model failed with exit 3. No implicit
model downloads, capture, provider or account/config discovery is added.

Blank cues must agree in JSON and SRT too, including their timing and order;
unmatched or backward empty SRT cues are rejected. This preserves the upstream
initial blank cue without silently ignoring extra cues. Explicit ordinary files
must remain stable under one owner for the run. Pre/post hashes detect persistent
changes; they are not isolation against a concurrent writer changing and restoring
paths or bytes.

Use the machine's recorded explicit arguments, then provide `--source` and a new
`--output` directory, finite `--threads`, `--timeout` and `--max-seconds` bounds.
[SOURCE-RECIPE.json](SOURCE-RECIPE.json) preserves source/build/model identities and
the input/output contract. Another machine's source build needs its own admitted
binary hash; identical build bytes across machines are not claimed.

A transcript-informed acceptance clip retained both complete contrasting clauses,
trimmed only the introduction, padded 120ms before the first selected word, and
re-timed phrase captions. Every output audio sample matched the selected source
interval. This establishes a working transcript-to-clip path on that public sample,
not a general semantic-highlights or phoneme-boundary guarantee.

## Native editable timeline

The existing Blender route saved a paired video/audio sequence as `.blend`, reopened
it in independent clean processes, shortened one clip by a frame in a separate
copy, and rendered the original and edited boundaries. The 30fps synthetic project
mapped external frame0 to Blender frame1 and preserved the original project hash.
Use the recorded runtime and `blender-production-workflows` method; keep referenced
source media alongside the editable project.

Native WAV mixdown in this fixture produced 192512 stereo sample frames at48kHz,
including a 512-sample silent tail. Native sample-exact delivery therefore remains
failed. A separate strict post-export gate verified every discarded tail byte was
zero before creating a new 192000-sample WAV; a nonzero-tail mutation was rejected.
FFmpeg then encoded all120 freshly rendered native frames with that corrected PCM.
All129 delivery checks passed, including source-frame geometry, full decode,
4-second timing and exact delivered audio bytes. This is a verified post-export
route, not a repaired or universally sample-exact Blender native exporter.

## Alternatives researched

- [LosslessCut](https://github.com/mifi/lossless-cut/blob/master/docs/troubleshooting.md)
  is useful for fast human segment review. Keyframe cuts can begin early; smart cut
  is experimental. Verify actual exported boundaries before claiming frame accuracy.
- [Kdenlive](https://docs.kdenlive.org/en/effects_and_filters/speech_to_text.html)
  offers configured Vosk/Whisper subtitles and transcript-driven clip selection.
  It is an open-source fallback if a concrete existing-editor gap justifies setup.
- [Shotcut](https://www.shotcut.org/features/) offers editable MLT projects, mixed
  formats, subtitles, transitions and audio tools. It overlaps an installed NLE;
  commissioning another editor is optional, not proof of a better integration.
- [OpenCut](https://github.com/OpenCut-app/OpenCut) is undergoing a rewrite. Its new
  editor API, MCP and headless architecture are announced work; do not treat them
  as a finished automation foundation. Upstream points users to classic today.

No alternative app, paid provider, account, cloud/GPU service or new model was
installed by this evaluation. [DISTRIBUTIONS.json](DISTRIBUTIONS.json) records the
separate existing full media distribution and the unadmitted auto-editor candidate;
it is provenance, not an installer or a claim that every platform is commissioned.
