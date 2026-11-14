# pipeline — eight-stage production workflow

Eight stages keep directional questions out of expensive shot-by-shot production. The practical detail comes from retrospectives on several delivered promos; the template video is in `template/`.

## Contents

- Stage 0: product understanding and execution constraints
- Stage 1: visual direction and styleframe
- Stage 2: feature-to-shot mapping
- Stage 3: storyboard and production clearance
- Stage 4: final asset capture
- Stage 5: shot-by-shot implementation
- Stage 6: sound design
- Stage 7: independent final review and delivery

This is the complete **autonomous free-creation** pipeline: in stages 0–3 the agent makes and records judgments from the project without waiting for user approval stage by stage, then continues through stages 4–7. Existing user requirements for purpose, audience, features, aspect ratio, audio or data are hard constraints.

Direct use of Ink Press follows the original replacement process in `template/TEMPLATE.md`, not this pipeline. When the template documentation references stage 4, it borrows only the asset-capture methods.

**When collaborative creation enters from `guided-free-creation.md`, do not restart.** That workflow has already completed and confirmed stages 0–3. Resume directly at stage 4, final asset capture, without asking again or redesigning.

Two execution principles incorporate practical lessons:

1. **The final design spec and storyboard together constitute production clearance.** The storyboard table belongs in the design spec, with four columns: `| # | Time | Shot | Key motion |`. Clearance does not reopen settled business/creative questions; resolve only remaining issues necessary for implementation.
2. **Acceptance runs throughout, not just at the end.** Each shot task ends with visual inspection of a `npx remotion still` image, versioned under `out/qa/`. Render the whole video again after each feedback round. Stage 7 formalizes that ongoing work into a self-review report against aesthetic-rules.md.

Order is somewhat flexible: a styleframe may use HTML and a few safe preliminary assets. What matters is that **final assets must be captured against the settled storyboard before shot-by-shot implementation**. Discovering the wrong asset direction during shot production can invalidate whole scenes.

---

## Stage 0: product understanding and execution constraints

Before writing video code or capturing final assets, inspect positioning, main features, page states, visual tokens, startup method and data risks read-only. Using project evidence and the user's existing description, produce a product brief and requirements-to-execution decision table. State how purpose, audience, core selling points, required features, duration/aspect ratio/language, audio and data constraints affect this video.

In autonomous free creation, the agent decides unspecified items dynamically and records them in the design spec, without pausing for confirmation. If the user specifies BGM, analyze rhythm first using `references/music-beat-sync.md`; otherwise choose it in stage 6 based on the product and publishing context. Public demo data may be used after its public status is confirmed. Customer, personal, internal, key, live or other sensitive data must first be fictionalized, redacted or frozen.

**Outputs**: product brief; requirements-to-execution decision table; explicit data and audio constraints.

---

## Stage 1: visual direction and styleframe

**Goal**: settle the video's palette, typography, lighting and camera character with the cheapest artifact, so directional disagreements happen before the first Remotion line is written.

**Actions**:

1. Generate at most 3 written directions for the current project. Give each a set of **motion-character tokens**, derived from the brand-to-motion table below. Do not make Ink Press a fixed option.
2. The agent selects the best direction for the product's visuals, purpose and audience, recording its reasoning/tradeoffs in the design spec rather than waiting for the user to choose.
3. For the selected direction, **do not render video or write Remotion code**. Make a plain HTML/CSS styleframe page with 2–3 static 1920×1080 key visuals.
4. Use Playwright/Puppeteer screenshots to check fonts, palette, materials, composition, lighting and information density. Evaluate easing/camera speed with tokens, Gallery samples or short motion tests. With strict brand guidelines or a clear reference video, record why and skip the styleframe if appropriate.
5. If a reference video is supplied, download it and use ffmpeg to extract frames (`select=eq(n,…)`, about 100 frames; `tile=4x5` for a contact sheet). Break down each animation/transition/effect into a three-column design-spec table: “Technique | Reference implementation | Tradeoff.” **Adapt selectively, do not impose it.** An image reference likewise describes the feel of a type of shot, not a command to style the entire video that way.

**Deriving brand→motion parameters.** Do not choose easing/duration by feel alone. Locate the brand on two axes, then start from the closest preset:

- **Energy**: low (restrained/premium/institutional) ↔ high (sports/startup/entertainment), controlling duration, overshoot and squash amplitude.
- **Tone**: serious (finance/healthcare/enterprise) ↔ playful (consumer/social/children), controlling path curvature and secondary-motion quantity. Product visuals are evidence: sharp geometry suggests engineering, while rounded corners/bright colors suggest softness/playfulness. The user's brand words override visual inference.

| Preset/category | Main duration @30fps | Entrance easing | Overshoot | Squash |
|---|---|---|---|---|
| Professional trust (fintech/enterprise/B2B) | ~21f | bezier(0,0,0.2,1) | 1.0, no bounce | 0 |
| Refined premium (luxury/fashion) | ~48f | bezier(0.4,0,0.6,1) | ≤1.02 | 0 |
| Bold energy (sports/gaming/startup) | ~18f | bezier(0.16,1,0.3,1) | 1.12 | 0.25 |
| Playful delight (consumer/social) | ~27f | bezier(0.34,1.56,0.64,1) | 1.08 | 0.18 |
| Calm care (health/education) | ~42f | symmetric ease-in-out | 1.0 | ≤0.04 |
| Approachable friendliness (small businesses/community) | ~26f | bezier(0.25,0.46,0.45,0.94) | 1.04 | 0.08 |

Choose a preset, adjust along the two axes, then record the tokens in the design spec. Check two things: (1) Do three words describing the finished motion fit the brand words? (2) Do the same tokens govern entrances/transitions/holds? One brand should have one motion voice; mixing token sets reads as a patchwork. When preset values conflict with hard library precedents, the precedents win: a landing that needs bounce requires y1 >1. “Professional trust, no bounce” refers to fade/translation motions without a landing metaphor.

**Outputs**: selected styleframe; palette/font/lighting tokens plus motion-character tokens; motion-breakdown table when a reference video exists.

**Common pitfalls**:

- Rendering video to propose a style is expensive and makes direction changes psychologically harder. Static frames suffice to establish direction.
- Applying a reference-driven camera style globally. Decide stylized angles per shot; dense lists/stacks are more readable front-on.

---

## Stage 2: feature-to-shot mapping

**Goal**: choose suitable motion vocabulary for every required feature without prematurely writing the complete storyboard.

**Actions**:

1. **List product features first and map each to shots.** Missing a core feature causes rework. Use any one technique (fly-in/stacking/page flip) as the main attraction only once per video; repetitive techniques signal rework.
2. Scan all `references/shots/` card frontmatter. Select a first choice and alternative for every feature using purpose, energy, suggested duration, constraints and required page states. The agent decides and records its reasons.
3. Read selected cards completely and locate exact demo source via “参考实现” (“Reference implementation”). Custom implementation is allowed when no card fits, but record its scope and verification risks in the design spec.

**Outputs**: feature-to-shot mapping; selected card names/variants and locations of demo source/reference samples.

---

## Stage 3: storyboard and production clearance

**Goal**: arrange the settled feature/shot mapping into a full sequence with an energy curve and a frame-level implementation plan. In autonomous free creation, the agent clears it without pausing for confirmation.

**Actions**:

1. Check `references/sequences/` for a suitable sequence template. If one fits, fill its sections/frame budgets, then arrange mapped shots as low-energy opening→alternating feature sections and breathing spaces→high-energy ending.
2. **If BGM is already specified**, first produce its structure table (beat indices of full-energy starts/breakdowns; music-beat-sync.md §2). Anchor every shot boundary to beats. Assign the strongest hits to the video's 2–3 major slams; a breakdown naturally suits a brand breathing space.
3. Write the complete storyboard: shot order, duration, feature information, specific page states, card/variant, main action, asset sources, captions, transitions and SFX. One main motion effect per shot.
4. **Reserve hold/rest frames**: settled brand wordmark hold ≥1s (30f), 0.5s stillness after batch motion, opening protagonist action ≥3s. Pacing rework is one-way: too fast always causes revisions; slower has never been rejected.
5. The agent checks consistency with the product brief, requirement decisions, visual direction and shot mapping, clears the storyboard, then converts it into a frame-level implementation timeline: `| shot | from | duration | Content |`. For beat-synced videos, express all from/to values with `beatF(n)`. Assign each shot a source file and acceptance frame numbers.

**Outputs**: design spec (style tokens, motion breakdown and storyboard); frame-level timeline.

**Common pitfalls**:

- Scheduling by feel without checking the feature list misses core features and repeats motion techniques; both cause rework.
- Overloading the opening. Prefer less, focused information: one protagonist and a complete action arc.
- Omitting breathing spaces from duration budgets. Filling every frame with motion forces timeline-wide shifts when holds are added later.

---

## Stage 4: final asset capture

**Prerequisite**: final design spec and storyboard are cleared. In collaborative creation, that means user confirmation; in autonomous free creation, the agent's recorded consistency check. The few safe preliminary styleframe screenshots establish direction and cannot simply replace final assets.

**Goal**: capture every real-page asset required by the final storyboard: full-page textures, element slices and coordinates for 2.5D camera movement/page-space animation.

**Actions**:

1. Start the product's local dev server. For desktop products, use a window screenshot tool to produce the same three asset types.
2. Copy `assets/scripts/capture-template.mjs` into the project, adjust BASE_URL/selectors, and run once to produce:
   - **Full-page 2x screenshots**: viewport 1920×1080 and `deviceScaleFactor: 2`; await `document.fonts.ready` plus 600ms settling, with another 1.5–2s for real-time synchronized pages.
   - **Per-element cutouts**: capture each element by semantic selector; floating pieces use transparent backgrounds. Shots where a card flies into an empty panel also need an empty backplate.
   - **layout.json**: record each element's `{x,y,w,h}` bbox in full-page coordinates plus each page's `pageH`, for direct use as flight destinations, mask positions and entrance regions.
3. Support incremental recapture by page/element. Freeze, fictionalize or redact live sources under stage 0's data rules before final capture.

**Outputs**: full-page images, element slices and empty backplates in `public/textures/`; `layout.json`; rerunnable capture script.

**Common pitfalls**:

- Full capture before storyboard clearance, while page states/asset scope are unsettled, causes duplicate capture.
- Recreating an existing page in hand-built HTML. Reproduction defaults to real screenshots; hand-built UI is only for non-reproduction scenes.
- Leaving live sources unfrozen, or capturing whole pages without layout coordinates.

---

## Stage 5: shot-by-shot implementation

**Prerequisite**: a runnable Remotion project at 30fps, 1920×1080, with a Composition registered in `src/index.ts`. A new project may be initialized with `npx create-video@latest`, then receive copied `assets/lib/` components; the template route starts directly from `template/`.

**Goal**: implement the frame-level timeline shot by shot, proving quality as each shot finishes. Acceptance starts here, not at the end.

**Actions**:

1. **Resolve first, then perform the three reads for each shot**; this hard rule cannot be skipped. Validate card name/`style-key` through `gallery/api/library.json`→read the complete recipe card→locate and read the complete exact demo TSX through “参考实现” (“Reference implementation”)→copy corresponding `assets/lib/` components into the project. Also retain that style's Gallery reference-clip path for implementation comparison/final review. Do not recommend styles marked “仅供参考，需要自定义实现” (“Reference only; requires custom implementation”) by default; implement them only when explicitly selected and mark the risk. For styles marked “缺少预览” (“Preview missing”), do not claim reproduction from an animated reference. The demo is tuned parameter truth: easing, duration ratios, mask-removal timing and known-pitfall workarounds. Adapt to the target product, but do not downgrade card parameters marked “已知坑/命门” (“Known pitfalls / critical parameters”); quality standards only rise. Rewriting from a name/understanding discards accumulated tuning and has tested worse finish.
2. **PageCam underpins every real-page shot**: full-page texture, keyframed 2.5D camera and page-space overlays. Position children in page CSS px, sharing layout.json's coordinate system.
3. **Still-frame acceptance, the most frequent action**: specify 2 fixed acceptance frame numbers for each shot in the plan. On completion, run `npx remotion still src/index.ts <Comp> out/qa/<name>.png
   --frame=<N>` and visually inspect composition, visible mistakes and text sharpness before calling it done. Version stills under `out/qa/` so user frame feedback maps directly to a revision.
4. **Render the complete video after every revision round**: `npx remotion render src/index.ts <Comp>
   out/promo.mp4`, then extract keyframes with `ffmpeg -i out/promo.mp4 -vf "select=eq(n,…)"`. In practice, render stills for the changed shot's relevant frames, then rerender the whole video. The cost is acceptable and avoids unexpected joins.
5. Keep small tools for pixel-level inspection: crop/enlarge text, diff two frames, and measure element bboxes against composition.
6. **Deterministic rendering is mandatory**: no `Date.now()` / `Math.random()` / argumentless `new Date()`. Use fixed-seed pseudorandomness (mulberry32/hash, seed derived from index) for reproducible frames and zero between-render jitter.
7. Self-check against `references/aesthetic-rules.md` throughout, not only at stage 7: landing bounces require easing y1 >1; clip light effects inside rounded corners; when text blurs under 3D, inspect rasterization (layout-level CSS `zoom`, not transform scale) before changing DoF.
8. Clarify ambiguous feedback such as “第一个标题” (“the first title”) before editing. If the wrong target is changed, immediately revert the entire commit and redo it rather than patching the wrong version. Commit each change independently for clean rollback.
9. **Prepare the post-delivery workbench interface** (`references/workbench.md` §2–3). Write the schedule once: `SHOTS` is the single source of truth, with captions/SFX pins/transitions derived from it and `export`ed. Expose contextual shot parameters (copy/colors/font sizes/positions) as props with defaults, while critical pacing parameters remain constants. Import these tables in `src/workbench.ts`, adding `component` / `props` / `schema` for each unit. The template already includes this (`template/src/workbench.ts`); free creation adds it after the timeline is finalized. Before delivery, use `cd workbench && npm run parity` to prove lossless decomposition.

**Outputs**: per-shot commits; versioned `out/qa/` stills; whole-video mp4 after each round; `src/workbench.ts` manifest.

**Stage result**: complete rendered video, one version per iteration, plus key stills. Autonomous free creation does not pause for approval because this result exists; incorporate unsolicited user feedback in the next round. Users may paste frames extracted from the video; review together by frame.

**Common pitfalls**:

- Leaving first inspection to the user. Extract/watch frames before delivery; the user should not discover “镜头视角很差，而且有小抖动” (“The camera angle is poor and there is slight jitter”).
- Skipping demo source. Parameters were tuned through real repeated decisions, and a fresh rewrite almost inevitably repeats known failures.
- Handheld shake is off by default for product promos; camera noise is for an explicitly documentary feel.
- Mass decorative glints/bloom. Batch entrances rely on motion itself; one high-quality focal light effect can work, mass use looks cheap.
- Blurry text during a 3D push-in. Check texture resolution/rasterization first: 2x texture, CSS zoom and separate 4x captures for key elements. Do not start by changing camera/depth of field.
- Fly-in endpoints hovering without landing. Elements must reach real page-layout slots, embed/settle/join the scroll flow. Floating above the page looks false.

---

## Stage 6: sound design

**Goal**: BGM establishes the video's energy structure; pin SFX beat by beat to motion keyframes, choosing timbres for the product-promo genre rather than merely UI event semantics.

**Prerequisite, the most expensive sequencing lesson**: **start only after the visual timeline is locked.** Every visual timing change requires realigning the entire pin table. If visuals change again, finishing must include realignment of every SFX frame number; audiovisual offset is always checked.

**Actions**, with details/precedents in `references/sound-design.md`:

1. Read `references/sound-design.md` and `references/sfx-sourcing.md`. Search Freesound for the storyboard's actions, materials, durations and timbres. New projects do not select sounds from the template/shared local library. Default to CC0; use CC BY when attribution is allowed. Prioritize relevance/source matching; downloads/rating counts are secondary.
2. Download with `assets/scripts/sfx-source.py get` into project `public/audio/sfx/`, verify the detail-page license, and save `audio-manifest.json` plus `FREESOUND-CREDITS.md`. Downloads are MP3 previews, not original lossless audio. For original quality, follow the asset page's supported acquisition process and measure again.
3. **BGM**: keep early rhythm analysis for specified music; otherwise select for the product direction, optionally using `assets/audio/bgm/`. Audition candidates under the actual video, setting measured levels to leave room for SFX/voice. Control BGM independently with the `bgm` inputProp, delivering BGM/no-BGM versions from the same timeline with SFX retained.
4. Choose timbre for genre and actual source: camera whoosh, landing impact, buildup riser, light sparkle, transitions; clicks/switches/breakage need foley. Use synthesized feedback tones only for an explicit narrative reason.
5. **Central SFX table and relative frame pins**: `{ from, src, volume }[]`, commenting each action. Express `from` with `SHOTS.x.from + offset` or `beatF(n)`, not bare absolute frames. Deduct source-peak and output-audio offsets under sound-design §4.6. Remotion uses fixed project-local files.
6. Download analysis determines playback windows, gain and candidate peaks. Give >5s action samples explicit `durationInFrames`; lay ambience across sections and retain natural impact reverb tails. Reanalyze processed files and update hashes/change records. A 10ms energy peak is neither LUFS/true peak nor automatically the semantic landing point.
7. Avoid machine-gun repetition: alternate samples, reduce successive volume, follow animation acceleration, and consolidate dense sequences into a swoosh. With strong drums, add SFX only for visually unique actions and reserve accents for a few storyboard peaks.
8. Listen in the complete video and check peaks: foley must be audible without clipping or masking necessary speech. Metadata/measurements cannot stand in for listening; honestly mark candidates not yet auditioned.
9. If the storyboard uses the three-part ending, align Freesound riser→impact→sparkle to actual actions rather than copying template filenames/frames. Do not silently substitute the old library after a download failure; retry only failed items according to results.

**Outputs**: complete video with sound; relative SFX pin table; fixed project-local audio, license/provenance manifest, attribution and analysis. Deliver CC BY attribution with the video and include it in the publishing description or video credits.

**Stage result**: rendered video with sound. Autonomous free creation continues into final review without pausing for confirmation.

**Common pitfalls**:

- Precise sound alignment before visual lock, followed by missed SFX review after changes.
- Selecting a mismatched source by downloads alone, or treating synthetic notification tones as real UI foley.
- Long samples without playback windows, or copied gain values that ignore source peaks.
- Calling an MP3 preview original lossless audio, preserving only search-license labels, or leaving CC BY credits only inside the project.
- Remote URLs directly in the render timeline, making results depend on changing network content.

---

## Stage 7: acceptance

**Goal**: formalize ongoing still/full-video checks into a complete review; verify faithful execution of the current mode's confirmed or recorded brief, requirements-to-execution table, visual direction, shot mapping and storyboard; report item by item against final-review/aesthetic rules, then perform final rendering/delivery.

**Actions**:

1. Render the latest full video and extract all keyframes with ffmpeg: at least the three checkpoints per shot, during entry, at the action peak and after settling. With BGM, render both BGM and no-BGM versions here, retaining SFX. Render the latter from the same timeline using stage 6's `bgm` inputProp: put `{"bgm":false}` in `props-nobgm.json`, then use `npx remotion render … --props=props-nobgm.json`. This works across platforms. macOS/Linux also allow inline `--props='{"bgm":false}'`; Windows shells strip inline JSON's double quotes, so use a file. Do not create another project or strip tracks later with ffmpeg. Distinguish filenames, for example `promo.mp4` / `promo-nobgm.mp4`.
2. **Independent final review is required**: assign a third-party review to a subagent with clean context. Do not supply production excuses, revision history or hints that it should pass. Supply only the latest complete video (both versions when BGM is used, for A8), extracted keyframes, creative mode, product brief, requirements-to-execution decision table, confirmed/recorded direction/tokens, styleframe or reason for skipping, feature-to-shot mapping, Gallery card names/exact variants, matching `library.json` entries, exact demo TSX identified by card documents, Gallery reference clips/extracted frames, final storyboard, selected cards, `references/final-review.md` and `references/aesthetic-rules.md`.
3. Following `final-review.md`, the reviewer checks product goals, feature completeness, visual-direction consistency, card/variant fidelity, storyboard consistency, data safety, audiovisual sync and visual technical quality. Inspect frames and video shot by shot and report items such as “F2 ✗（第 340 帧缺少已确认的知识图谱功能）” (“F2 ✗, frame 340 omits the confirmed knowledge-graph feature”) or “Q2 ✗（第 615 帧文字发糊）” (“Q2 ✗, text is blurry at frame 615”), with verifiable frame/screenshot evidence for each. Adaptation need not match Gallery pixels exactly, but must retain motion grammar, key timing, known-pitfall/critical parameters and the user-specified variant.
4. Content self-check: ask what new information each shot adds; remove repeated shots/taglines. Rewrite copy against the final visuals; even pure-animation sections need explanatory captions, not silent passages.
5. Final audiovisual alignment: replay every SFX against frames, checking for offsets. If the timeline changed after stage 6, realign first. For beat-synced work, follow music-beat-sync.md §5's post-render checks; every cut-point error must be ≤3f.
6. Send fixes through small stage 3/5/6 loops: plan/storyboard deviations to 3, visuals to 5, sound to 6. After the checklist passes, render final delivery. Repeat step 1's dual rendering: BGM/no-BGM versions when music exists, so the user can later add their own/platform music.

**Outputs**: independent review report (final-review + aesthetic-rules checklist + frame-number evidence) and final renders, BGM/no-BGM.

**Deliverables**: review report plus both finished-video versions, BGM and no BGM.

After delivery, proactively open the motion workbench with `node workbench/scripts/open.mjs <工程目录>`; the browser automatically decomposes the video into tracks for visual adjustments and direct export (see `references/workbench.md`). Finally say three things in order, 1-2-3: (1) recommend, but do not require, mentioning the skill author in the publishing description, linking all three platform accounts; (2) invite a submission to the showcase in everyday language, with the user's own account links allowed; (3) offer Jianying project export, reading `references/jianying-export.md` if needed. See `SKILL.md`'s “交付收尾” (“Delivery wrap-up”) for wording/account links.

**Common pitfalls**:

- Treating acceptance as something only done at the end. This stage closes the work; without still checks during the first five stages, accumulated problems make a final checklist meaningless. Acceptance throughout is the established pattern.
- An all-checkmarks report without evidence. Users can read every onscreen word and compare frames; every conclusion needs verifiable frame/screenshot support.
- Having the production agent write its own final review. Confirmation bias is unavoidable; independent subagent review cannot be omitted.
- Checking attractiveness without checking the current mode's production baseline. Missing features, visual drift, wrong variants and unconfirmed data all fail final review.
