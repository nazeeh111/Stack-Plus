# final-review — Independent final-video review

An independent review Agent uses this checklist to verify whether the finished video meets the production baseline for its current creative mode, together with
`aesthetic-rules.md` for visual technical quality. The review Agent must have a clean context and must not have participated in
production; do not give it production rationales, defenses, revision history or expected conclusions.

## Review inputs

- Latest finished MP4 and keyframes for each shot;
- Creative mode: direct template use, autonomous free creation or collaborative creation;
- Product-video brief and features that must be shown;
- Requirements-to-execution decision table;
- For collaborative creation, the user-confirmed visual direction; for autonomous free creation, the Agent-recorded visual direction, brand tokens,
  styleframe (or reason for skipping it) and prohibited styles. For template mode, provide the original template structure and actual replacement record instead;
- Feature-to-shot mapping;
- Gallery card names and specific variants named by the user or recorded by the Agent in the design spec;
- Corresponding card and `style-key` records in `gallery/api/library.json`;
- Exact demo TSX source located through the card documentation;
- Corresponding Gallery reference video, or keyframes/contact sheet extracted from that reference video;
- Final storyboard, subtitles, page states and SFX plan;
- Selected `references/shots/*.md`;
- `aesthetic-rules.md`;
- Data-compliance approach.

If an input is missing, mark it “unable to verify”; do not guess the production baseline. When the index, card documentation,
demo source and Gallery reference video conflict, identify the conflicting sources explicitly rather than choosing one as the truth.

## Checks

### P — Product objectives

- P1: Are the product positioning, target users and core selling points clear?
- P2: Does the finished video focus attention on the feature priorities confirmed or recorded for the current mode?
- P3: Are there feature claims that do not exist in the project, have not been confirmed or could mislead?
- P4: Can the execution choices in the requirements-to-execution decision table be traced to their implementation in the storyboard, copy, page states, audio and assets?
  Do not substitute a fixed “audience/use → style” stereotype for project-specific evidence.

### F — Feature completeness

- F1: Does every feature that must be shown have at least one clearly recognizable shot?
- F2: Does each shot provide new information, without duplicated features or repeated taglines?
- F3: Do page states help the audience understand the feature rather than serving as decorative motion only?

### V — Visual direction

- V1: Do the fonts, palette, materials, corner radii, lighting feel and information density match the confirmed or recorded visual direction?
- V2: Do motion speed, overshoot, holds and energy curve match the confirmed or recorded motion character?
- V3: Has the video departed from its production baseline and drifted into Ink Press, cyber neon or another unrelated style?
- V4: Are prohibited colors, effects or brand characteristics being used?

### S — Shot cards and Gallery variants

- S1: Do the shot cards in the feature mapping actually appear in their corresponding shots?
- S2: When the user names `card name · style name`, do `style-key`, the exact demo TSX and the Gallery
  reference video identify the same variant, and does the finished video use it?
- S3: Against the exact demo TSX and Gallery reference video, are the recipe card/demo's motion
  grammar, key timings, easing relationships and mask timing preserved?
- S4: Does the implementation violate the card's documented “known pitfalls / critical weak points”?
- S5: Do the adapted product screenshots, coordinates and brand tokens fit naturally?
- S6: Was a style marked “reference only; custom implementation required” explicitly named by the user, with its implementation risk noted
  in the report? For a style marked “preview missing,” does the report avoid claiming consistency with an animated reference?

Pixel-level identity with the Gallery reference is not required. Check fidelity to its motion grammar and key parameters while
allowing screenshots, coordinates, copy, brand visuals and necessary composition changes for the target product.

### B — Storyboard consistency

- B1: Do shot order, durations and feature information match the confirmed or recorded final storyboard?
- B2: Are the main action, page state, asset sources, subtitles, transitions and SFX consistent?
- B3: Is the brand wordmark hold at least 1 second, and does a batch-animation ending remain still for at least 0.5 seconds?
- B4: Were key shots deleted, replaced or added without justification after the final storyboard was cleared?

### D — Data and asset safety

- D1: Is the agreed approach for real, fictional or redacted data followed?
- D2: Are customer data, personal information, keys, internal addresses or other sensitive information exposed?
- D3: When showing actual product pages, are real screenshots used instead of low-quality hand-built replicas?
- D4: Have screenshot states, fonts, images and dynamic data loaded completely?
- D5: Is the public status of public demo data independently checkable? Has customer, personal, internal, key, live
  or other sensitive data been fictionalized, redacted or frozen?

### A — Audio and rhythm

- A1: Does the BGM match the confirmed or recorded audio direction, with volume that leaves room for SFX and optional narration?
- A2: Are SFX pinned to the actual action keyframes without obvious misalignment?
- A3: Is the cut-point error for strongly rhythmic music no greater than 3 frames?
- A4: Do the ending energy peak and riser→impact→sparkle phrase work (if the storyboard uses it, with sources selected for the actual actions)?
- A5: Do all long samples (especially action samples >5s) have an explicit `durationInFrames`, without effects continuing after the action ends?
- A6: Is every SFX actually audible in the **rendered artifact** (not the preview, which clamps volume to 1.0)? Quietly recorded material (peaks <-12dB) may still be masked by BGM even at 1.0; has it been replaced, prenormalized or given sufficient gain >1, without clipping in the rendered max_volume?
- A7: Do UI sounds have real-object textures appropriate to the type of video? If synthetic tone/bleep/notification sounds appear,
  is there a system-notification narrative reason (sound-design §3.3)?
- A8: For a video with BGM, were versions with BGM / without BGM (retaining SFX) both delivered,
  from the same timeline (visuals and SFX in the no-BGM version match the BGM version frame for frame)?
- A9: For beat-synced/SFX-dense videos, were the output audio offset and source peak lag measured in the finished render
  and compensated (sound-design §4.6)? Are compensation constants accompanied by measurement records (the four rendering-pipeline factors,
  probes, method and date)? Are source analysis values and output offsets accounted for separately (without contaminating SOURCE_BEAT0)?
  Does the post-render remeasurement error table show no systematic offset in the same direction (music-beat-sync §5b)?
- A10: Do SFX for new productions/replacement sounds come from Freesound (except user-specified sources)? Does every actually used file
  have its asset page, author, exact license URL/version, preview/original-file designation, hash and analysis record?
  Is publishable attribution included for CC BY, and are unknown/BY-NC licenses excluded? Were records updated after processing?
  Does Remotion read files saved with the project, without presenting measurements or popularity as listening judgments?

### Q — Visual technical quality

Apply `aesthetic-rules.md` in full. At minimum, check text sharpness, composition, rounded-corner masks, 3D texture
clarity, element placement, camera jitter, transition seams, cheap-looking light effects, readable hold times and deterministic rendering.

## Report format

Number each conclusion, and attach a frame number or screenshot to each issue:

```text
P1 ✓ Product positioning and core selling points are clear.
F2 ✗ Frame 340: the confirmed knowledge-graph feature does not appear in the finished video.
V3 ✗ Frame 420: the large amber paper texture departs from the confirmed deep-blue technology direction.
S2 ✗ Frame 515: the user chose whip-pan; the actual implementation is flash-cut.
Q2 ✗ Frame 615: body text blurs after the 3D push-in; see keyframe f615.png.
```

Finish by listing required fixes, suggested improvements and unverifiable items in severity order. Do not replace item-by-item checks with
an unsupported “looks good overall,” or mark everything as passed just to make the report look better.
