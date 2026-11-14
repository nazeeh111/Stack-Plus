# Freesound SFX sourcing

For new productions and replacement sounds, obtain SFX directly from [Freesound](https://freesound.org), not the shared local SFX library.
User-specified sound sources still take precedence. BGM follows its separate selection process; see [sound-design.md](sound-design.md) §2.
This module covers selection, downloading and provenance records; continue to follow sound-design for frame pinning, mixing and output-offset compensation.

## 1. Translate the visuals into sound requirements

For each cue, record the corresponding shot/action, sound source or material, target duration, attack/tail, timbre and licensing requirements.
For example, a paper-card slide-in: `paper slide`, 0.2–0.8s, dry, single action, no long tail, CC0.
Prioritize the source match, then compare duration, recording description and popularity; do not search only abstract moods or a broad term such as `click`.

- Do not choose a long recording containing several actions for a single click/slide unless the required action can be cropped out clearly.
- Download counts and rating counts help rank candidates but do not replace suitability; a 4.4 rating from many reviewers is usually more informative than
  6 people awarding 4.9. Cite actual data when recommending; leave missing values unknown rather than inventing them.
- Uploader descriptions provide clues about the source, equipment and processing; favor clear descriptions of actual sources that match the need.
  Famous equipment does not guarantee quality, nor do mouth-made sounds or built-in microphones automatically make a sound unusable; judge against the project's texture.
- Assess real-world Foley for UI actions separately from synthetic notification sounds, following aesthetic-rules S1/S4.

## 2. Search

The script is independently implemented with the Python 3.9+ standard library and needs no Freesound API key; downloading/analysis requires ffmpeg and ffprobe.
Run it from the skill root; quote paths containing spaces. If installed elsewhere, use the script's absolute path.

```bash
python3 assets/scripts/sfx-source.py search "paper slide" --max-duration 1 --limit 5 --output /path/to/video/audio-search.json
python3 assets/scripts/sfx-source.py search "short cinematic impact" --license by --max-duration 3 --pages 2
```

The output JSON includes ID, title, author, asset page, preview URL, description, duration, downloads, rating and rating count.
It preserves search-relevance order and filters license and duration again locally. `--pages` is capped at 3 pages; narrow the keywords first
rather than substituting more page scraping for selection. Search output is for comparison only, not proof of the license at download time.

The default license is `cc0`; `by` permits CC0 and CC BY. Commercial product videos do not accept BY-NC, Sampling+ or unknown licenses.
When the user accepts attribution, use `--license by` without repeatedly asking for every sound.

## 3. Download into the current video project

Replace the IDs with candidates returned by this search; `get` also supports known IDs and does not depend on a global cache.

```bash
python3 assets/scripts/sfx-source.py get fs:12345 fs:67890 --out-dir /path/to/video/public/audio/sfx
```

For CC BY, also pass `--license by` to `get`. Before downloading, it rereads each asset's detail page,
checks the actual license URL/version, then downloads with bounded concurrency. It does not change network proxies or switch automatically to another sound source.

Outputs:

- `fs-<id>.mp3`: Freesound's high-quality **lossy MP3 preview**, not the uploader's original WAV.
- `audio-manifest.json`: source, author, asset page, license URL/version, preview designation, download time,
  SHA-256, change record and actual audio analysis.
- `FREESOUND-CREDITS.md`: source and attribution list for project delivery. CC BY entries must appear in release-page notes
  or the video's credits, not remain only in project files. Record edits, speed changes, normalization and other changes in `changes`.

Repeat downloads check file hashes and do not overwrite independently modified files or same-named files of unknown provenance. Run only one
`get` at a time in each output directory. When some downloads fail, successful items retain manifest records and the command exits nonzero; retry only failed IDs based on the per-item results.
If no candidates match, adjust the query. On timeouts, rate limits or page-structure changes, stop automatic calls to that source and explain the specific problem.
Offer asset-page links for manual downloads if useful, then record provenance using the same fields; never pass off an HTML error page as audio.

When original quality or lossless processing is explicitly required, obtain the original through Freesound's supported sign-in/download process on the asset page;
do not convert a preview to WAV and label it original lossless material. Record the actual file kind, URL and hash, then analyze it again.

## 4. Analyze, audition and integrate

`get` automatically uses ffprobe and ffmpeg to decode and validate the file, recording its actual format/sample rate/channels, duration, sample peak,
overall RMS, the peak of the RMS energy envelope in 10ms windows and active intervals relative to peak -40dB. These are not LUFS, true peak or exact action onsets.
For a recording of multiple actions, select the correct peak rather than applying the file's largest peak to every cue.

Analyze a processed file separately:

```bash
python3 assets/scripts/sfx-source.py analyze /path/to/video/public/audio/sfx/fs-12345.mp3 --output /path/to/video/audio-analysis.json
```

After processing, update the manifest's filename, SHA-256, `analysis` and `changes`; record peak times separately for the original and processed files.
Audition in the browser or under the video segment to check timbre, background noise, tail and relationship to the music.
When the available tools provide only metadata/measurements, explicitly state “not auditioned”; do not describe download counts, waveforms or ffmpeg analysis as listening impressions.
For autonomous creation, select based on the evidence and continue; when the user asks to hear candidates, provide asset pages or a supported local audio preview.

Then connect the fixed files to the central SFX table, derive `from` from `SHOTS`/`beatF`, and compensate for
source peaks and output offset using sound-design §4.6. Downloaded files must remain with the project; do not reference only remote URLs.
The workbench displays project audio; after new downloads, rerun `node workbench/scripts/open.mjs <PROJECT_DIRECTORY>` to update the index.

## 5. Templates and delivery

Historical files in `template/public/audio/` are retained for unchanged runs and verification, not as a selection pool for new projects.
When using a template for a new product, retain the SFX action semantics and frame-pinning structure, select sounds from Freesound, then remeasure and align them;
when the user explicitly requests reproduction of the original sound, retain that requirement and verify its source against the template's licensing records.
The full record from before removal of the shared SFX directory is available in Git history; BGM licensing remains in `assets/audio/ATTRIBUTION.md`.

Deliver the audio files, manifest, attribution list and SFX schedule. See [final-review.md](final-review.md) A10 for the final check.

The sourcing method references [vibe-motion/sound](https://github.com/vibe-motion/sound) (reviewed version `01f81d6`);
this repository's CLI is independently implemented and does not incorporate its scripts or personal Clash configuration.
