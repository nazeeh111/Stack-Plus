# Aesthetic rules (case-based)

Source: precedents distilled from practical revisions of several promo films (finished-film templates are in `template/`).

**How to use**:
- Each entry = a rule (one actionable sentence) + a case (the user's words / revision history) + self-check questions. All three are required.
- At pipeline.md stage 7 acceptance, **check every entry** and output a self-check report in the form `编号 ✓` or `编号 ✗(位置)` (编号 = ID; 位置 = location, meaning shot name/frame number).
- Rules may be deliberately broken for a style, but every departure must be recorded in the project's explanatory document, stating which rule and why.
- ID system: R(pacing) / Q(material quality, camera movement, composition) / S(sound) / C(copy) / P(process). Published IDs are never reordered; append new entries only.

## Contents

- Pacing (R)
- Material quality, camera movement and composition (Q)
- Sound (S)
- Copy (C)
- Process (P)

---

## Pacing (R)

### R1. Let key information breathe after it settles; hold the brand wordmark for a full 1 second
Rule: once an information-bearing element (title card/number/full grid view) settles, keep it still for ≥1s before cutting. Give breathing pauses first to brand memory points (the moment the wordmark settles), not ordinary content cards.
Case: the user said, “Hold for one second after the first title appears,” then clarified, “Not the first title card. I mean the animations where AI field lab appears at the beginning and end; extend the hold by 1 second after it appears.” The pause was first applied to the wrong object, reverted, and redone. The final decision was a full 1-second hold for each opening and closing wordmark.
Self-check: does every image the viewer should remember have a complete still moment? Is the pause assigned to the brand/key information, or casually to an ordinary element?

### R2. Speed comes from acceleration, not fast constant motion; give group movement a physical metaphor and end with a 0.5s pause
Rule: fly-ins/scrolls always use nonlinear easing and uneven staggering; constant motion reads as cheap slides. For many similar entering elements, use a hard-accelerating beat that gets faster and faster, preferably tied to a physical metaphor such as dealing cards. Hold still for 0.5s after the board fills, then cut to the next beat.
Case: the user said, “As the cards keep stacking downwards, they should get faster and faster, and the scroll should get faster too, with a 0.5-second pause at the end,” and “The final speed is still not fast enough… the cards should automatically fly to their positions in order, settling faster and faster.” An accelerating scroll plus a 0.5s hold became a hard-accelerating card deal. An abstract flood did not converge after five rounds; the dealing metaphor passed in one.
Self-check: is any element moving in a straight line at constant speed? Does batch entry accelerate, and is there a still breathing moment at the end?

### R3. Prefer slower pacing: slow the first draft one notch, give the main action arc ≥3s, and demonstrate interaction at human speed
Rule: the opening hero action (focus → hover → return, as one complete arc) lasts at least 3 seconds. Simulated real interaction (typing, filtering, clicking) follows the speed of an actual person so viewers can follow along. Reserve hold/rest frames when laying out the timeline; the first draft is almost always too fast.
Case: all six independent rounds of feedback on the film asked for “slower/hold”; none asked to speed it up. The user said, “The first shot is still too fast; slow it to 3 seconds,” and “Typing in the search box and then filtering the cards happens too quickly; slow it down.” The opening was gradually slowed to a 3s macro opening, and the interaction section became an unhurried type-and-filter.
Self-check: watch each shot as a first-time viewer. What is too fast to see? Can you follow the interaction yourself?

### R4. Beat sync constrains timing, not amplitude: use whole-frame beat impacts at ≤3 points in the film; animate only the element layer by default
Rule: cutting on the beat in a strong-rhythm BGM film does not mean hitting the whole image on every beat. Impacts on the whole frame/camera layer (whole-frame scale pumping/shake/flash frames/negative frames) count as major slams: ≤3 in the film, pinned to the strongest-hit list in music-beat-sync §2b, with ≥16 beats between adjacent uses. All other beat animation affects only the hero element layer. A beat-pump burst lasts ≤4 beats, with ≤1 burst in the film. The kick-hit table is a candidate pool, not a trigger. **Count one technique/set-piece use, not its internal subevents**: one use of a card (a paparazzi triple flash or trailer-bumper three-cut sequence) takes one slot. The card's own burst structure and whole-film usage cap still apply; this rule does not count it again frame by frame.
Case: user feedback (2026-08-22): “When music is provided, the camera shakes with the rhythm, which hurts the viewing experience.” The cause was treating music-beat-sync's kick-to-impact mapping as whole-frame pumping on every beat. In a strong-drum track, kicks occur almost every beat; adding each “hit” to the camera layer creates beat-frequency image shake. This is related to Q3: Q3 blocks noise-driven handheld shake; this rule blocks beat-driven shake.
Self-check: replay any continuous 8 beats of a high-energy section frame by frame. Is whole-frame scale/position pulsing every beat? Count impacts on the whole-frame/camera layer across the film: more than 3? Does each match the strongest-hit list?

---

## Material quality, camera movement and composition (Q)

### Q1. Reproducing an existing page requires real screenshots; hand-built UI is limited to other scenes and must meet quality/clarity standards; handle data by its agreed risk scope
Rule: for any shot showing an existing product page, start by capturing the real page with a headless browser (full-page texture + element cutouts + coordinate json), rather than recreating it with hand-built imitation textures. Hand-built UI is allowed for scenes that do not reproduce an existing page (abstract openings/brand sections/standalone components absent from the page), but publication-level quality (Q10) and immediately clear meaning are hard requirements; otherwise return to screenshots. Public demo data may be retained only when explicitly confirmed by the product brief. Customer, personal, internal, key, live or other sensitive content must first be fictionalized, redacted or frozen. The same scope applies to hand-built assets.
Case: the user said, “I want the real page with animation added,” and “Do not use real data; make a fake set, and do not mention customer names.” Rebuilding from the real dashboard page invalidated the whole hand-built texture imitation made that afternoon. Revision (user ruling, 2026-07-13): “It does not all have to come from real page screenshots; hand-built UI components are fine, as long as quality and clarity of expression are assured.” The precedent was narrowed to “do not hand-recreate an existing page.”
Self-check: for each UI asset, is it reproducing an existing page? If so, it must come from a screenshot. Can a hand-built component pass Q10-level scrutiny for quality and clarity? Does its source data follow the confirmed data scope and exclude unauthorized customer, personal, internal or key information?

### Q2. Rasterize UI textures at native size before downscaling in 3D; investigate the texture-resolution chain first when text is blurry
Rule: rasterize UI textures for 3D scenes natively at 2–4 times their displayed size, then downsample in 3D. Enlarge through layout-level CSS zoom rather than transform scale. For blurry text, inspect rasterization first, not camera/DoF settings.
Case: the user asked three times: “The cards have clearly become blurry,” “Still not high definition enough… there are blocks of pixels,” and “The text clarity in the first shot is still unresolved.” Adjusting DoF treated the symptom without success. Rasterizing at native size produced genuine 4x sharpness; extending CSS zoom to every 3D page layer resolved the issue.
Self-check: capture frames from enlarged/perspective shots and inspect text edges. Are there pixel blocks? Is the source texture resolution ≥2 times its displayed size?

Technique details (the former hires-rasterize-3d-text technique card is retained here; reference implementation: template/src/aifl/live/PageCam.tsx):
- **Cause**: Chromium rasterizes a 3D composited layer at 1920 layout width and then enlarges it on the GPU. Downsampling first and enlarging later inevitably blurs the content, regardless of camera/depth-of-field parameters.
- **Solution**: use the CSS `zoom` property (layout-level scaling), not `transform: scale(zoom)`, so Chromium rasterizes at the enlarged device size and downsamples from a high-resolution source. Convert coordinates using `Tx = 960/zoom − cx` to keep framing consistent with the flat mode (the full derivation is in PageCam.tsx:100-114); omitting the conversion shifts the focus.
- **Companion settings**: full-page 2x (`deviceScaleFactor: 2`), separate 4x element screenshots for hero elements, and a 6f crossfade during the push-in to cover the lower-resolution page texture. A longer fade reveals the offset between the two layers.
- **Diagnostic order**: blurry text → inspect source texture resolution (screenshot scale → rasterization path → scaling method) before considering the camera. DoF creates atmosphere, never sharpness (unsuccessful in the recorded case). Verify by cropping and enlarging frame captures to inspect text edges; a thumbnail hides the issue.

### Q3. Keep the camera stable: product promos have no handheld shake by default
Rule: disable handheld shake in bright UI promos. Use only a tiny amount of camera noise in a dark atmospheric film explicitly seeking a documentary feel, and inspect rendered frames for unintended shake.
Case: the user said, “The camera angle is poor, and there is a small shake I cannot explain.” Removing handheld shake and recomposing led to no further shake complaints. Another dark atmospheric film retained shake=0.02 without complaint; this defines the inferred applicability boundary.
Self-check: inspect the rendered frames shot by shot. Is there any camera shake without narrative intent?

### Q4. Use highlights/sweeps sparingly: no mass application, at most once to the hero in a shot, clipped inside rounded boundaries
Rule: do not apply glint/sweeping-glow effects to every element. Batch entry should rely on motion itself rather than making each element glow. Any retained light effect must be clipped by its host's border-radius/overflow; light leaking beyond rounded corners is a typical source of a cheap look. This does not prohibit the whole technique: a single, well-executed sheen/glow on the hero can work. Inspect rendered frames and ask “Does it look good?” before delivery.
Case: the user rejected two versions: “Not every card needs to flash,” and “Remove the sweeping glow when cards appear; it does not look good.” Per-card glints and glow sweeps were removed, and chip highlights were clipped inside rounded boundaries. Clarification (user, 2026-07-13): the objection was that “the implemented version looks bad,” which “does not mean the technique/effect category is infeasible.” The mass-application ban and corner clipping remain, while glow/sweep techniques can be retried with a higher implementation standard.
Self-check: count glint/sweep uses across the film. Does any exceed one use on the hero element? Is every light effect clipped to rounded corners? Have you watched each retained effect at normal speed and found it attractive?

### Q5. Give the opening one hero: one subject and a complete action arc beat a group dance
Rule: keep opening information sparse and focused: one hero element, one complete arc (spotlight → push-in → hover → rim light → return). Many dancing elements do not establish a strong first impression.
Case: the user said, “The first shot only needs to focus on one card and give it more material quality.” The opening was rebuilt six times overnight; once the single-card structure settled, it remained unchanged through the finished film.
Self-check: how many things does the opening ask viewers to look at? Is the hero's action arc complete (beginning, development, landing)?

### Q6. Camera position serves readability: face dense information head-on; use a level side angle for text close-ups; validate stylized tilt shot by shot
Rule: decide stylized camera position for each shot. Narrative/emotional shots may tilt; dense lists/stacks stay frontal. Text-bearing card close-ups use a level side camera, avoiding steep low/high angles that harm readability. Never impose one camera style globally.
Case: the user rejected tilting the whole film: “It is not done well… the changes to the content list page [the paper list in the template film] are not good either; roll back.” The list page was individually reverted to a frontal view. The user then said, “Focus on one card… shoot it from the left rather than from below,” leading to a left-side hero camera.
Self-check: why is each tilted camera shot tilted? Is its text still readable at that angle?

### Q7. Four-part object close-up: tilted side angle, perceptible height, orbit, and a contrasting dark material background
Rule: build the environment for object/asset close-ups: a tilted side camera, a stack with visible volume/height, an orbit around the subject, and a dark material background contrasting with the main scene (such as brushed metal). Pull back while transitioning into the main scene.
Case: the user said, “The camera should shoot from a tilted side angle; the stacked items should have some height, and the camera should rotate around the stack. The entire scene should have a dark metallic background. Then as the camera pulls back, the dashboard background appears.” The pile orbit close-up developed into a dark brushed-metal background, a taller stack and an orbiting camera.
Self-check: does the close-up subject have volume and environmental contrast? Is the camera static, or does it orbit/pull back?

### Q8. End with a “launch-event group photo”: elements fly in from all directions around the wordmark, reaching the film's energy peak
Rule: finish a multi-feature product film with a family-photo structure: one representative element from every shown feature flies in from different directions and freezes. Match the film's peak energy (crane movement + stage lighting + particles). First-draft endings are almost always too conservative; increase one notch by default.
Case: the user said, “Core elements from each page fly in from different directions… forming something like a group photo,” and “Add more effects, animation and camera movement… like a product launch.” The assembled group photo grew into a launch-event finale with crane movement, stage lights and gold dust.
Self-check: is the ending the film's highest-energy point? Does the group photo represent every feature that was shown?

### Q9. Fly-in destinations must be real slots in the page layout; elements do not hover permanently over the page
Rule: after flying in, elements must embed in the page (settle in real grid slots and extend the scroll flow). Stopping above the page without landing looks false.
Case: the user said, “The research-question list should fly in from the air and embed in the dashboard,” and “Do not leave 10 project cards floating over it; keep scrolling down and arrange them below, without overlap.” Rows were made to fly into the layout, and the grid was rebuilt to extend with scrolling, nearly rewriting the entire file.
Self-check: does every settled fly-in element have a real coordinate in the page layout? Does any element remain floating above the page?

### Q10. Mock document content must meet publication quality: native typesetting, full text density, and the complete layout in frame
Rule: viewers can read every word on screen. Mock document/report shots must fill the product's native layout with realistic-density fictional content, with sidebars/comment panes fully visible. A “texture + slogan” fake document requires rebuilding the whole shot.
Case: the user said, “Use the existing typesetting and style for the weekly report, with only the content mocked. Fill it with text and show the complete left sidebar and right comment pane” (the template shot was a weekly report). The initial “texture + slogan” document was rebuilt as a fully mocked native layout with both side panes in frame.
Self-check: pause any document-shot frame. Does its content read as real? Is the layout complete (sidebars/comments/header)?

### Q11. Text meant to be read has a minimum effective height: captions ≥5% of frame height, supporting text ≥3%; measure final pixels, not fontSize
Rule: calibrate a 1080p film for phone/small embedded playback. Narrative captions need **effective height ≥56px (≥5.2% of frame height; 60px recommended)**, and subtitles/statistics/URLs or other supporting text ≥32px (≥3%). Effective height = fontSize × every ancestor scale × perspective compression (estimate 3D shots with `cos(rotY)`). Acceptance measures real pixels in rendered frames, not fontSize in code. Text has only two states: **“texture”** (decorative small text in screenshot cutouts, visibly blurred/dimmed so viewers do not try to read it), or **“to be read”** (adequate size and contrast, with a scrim/shadow over light backgrounds). There is no middle state of “re-typeset but still unreadable”; delete text that cannot be read. The closing URL/call to action is the line least suited to small type.
Case: the user (2026-07-25) said, “In several shots you can see that the accompanying text is very small… the text in those shots is now too small to see at all.” Review of the gallery promo found S1/S2/S4 captions at 38–40px (about 3.5% of frame height), an S6 secondary line at 30px and a closing URL at 25px, all below the limit. The S2 panel's subtitle “re-typeset for readability” was only 19px: the failed middle state. Raising all six areas to 60/40/34px passed the revision.
Self-check: take a frame from each captioned shot and reduce it to 480px wide to simulate a phone window. Can every sentence still be read? Measure actual rendered pixel heights for readable text: captions ≥56px and supporting text ≥32px? Is any text in the “intended to be read but unreadable” middle state?

---

## Sound (S)

### S1. Choose music and effects by film genre, not event: a strong electronic drum bed and cinematic SFX vocabulary; no game-pack timbres (the timbre is banned, not the action)
Rule: product-promo SFX vocabulary = whoosh(camera movement)/impact(landing)/riser(build-up)/sparkle(light effect)/transition. Exclude game-pack timbres. Choose strongly rhythmic electronic BGM with strong drums (tech-house-like), and audition candidates under the actual film; listening alone cannot establish the fit.
Case: the user said, “The music and sound effects sound too much like a game. Find something with strong drums and rhythm, and typical product-promo sound effects.” Mixkit tech-house plus whoosh/impact/riser/sparkle replaced all previously introduced Kenney CC0 game sounds. BGM changed three times in 34 minutes before the final choice was retained.

**The timbre is banned, not the action** (easy to misread; distinguish them): this rule rejects game-pack **texture** such as synth pluck/bloop, cartoon bounces and game-over scales, not “no sound for clicks.” An actual click/switch/break in the image should have its own foley, as S4 requires. Ask: does this sound like **that object in the real world** (shutter, mechanical switch, glass, paper), or **feedback from a game engine**? Use the former; discard the latter.
- The template itself uses `click-camera.mp3` at the film's highest SFX volume, 0.6: a real shutter, not a UI notification.
- Check Freesound UI results individually: real switch foley and synthesized confirmation/tone/bleep/
  notification often appear together. Use the latter only when deliberately portraying a system notification; see sound-design §3.3.
- Real glass, paper and other material sounds are foley; choose them for what the image needs.


Self-check: close your eyes and listen to the soundtrack. Does it resemble a product-launch teaser or a mobile game? Was BGM chosen after auditioning under the film? Does every UI sound have real-object texture or game-feedback texture?

### S2. Pin SFX to frames beat by beat; for rapid repeats, alternate two samples, step down volume, and accelerate intervals instead of repeating at the same loudness
Rule: centrally manage SFX in a declarative “frame + source + volume” table, with a comment identifying each visual action. Do not place effects by feel. Avoid machine-gun repetition for a series of similar elements with three measures: alternate two samples, reduce volume in steps along the sequence (such as six levels from 0.40→0.25), and accelerate intervals with the animation curve. Once they blur together, fade into a swoosh. This repository's recorded implementation used no playbackRate pitch shifting; pitch variation is not its repetition remedy.
Case: the user said, “When each week appears in the weekly report's left sidebar, you can use a different sound effect matched to its appearance” (the template's weekly-report page). A frame-pinned SFX table was established and retained to final delivery, then two pluck samples alternated as intervals accelerated from 8→3f. The six per-week pops finally stepped down from 0.40→0.25.
Self-check: is each SFX pinned to a specific frame with its action commented? Does the repeating section sound like a countable rhythm or mechanical repetition?

### S3. Do sound after picture lock; whenever the timeline changes, repin the entire SFX table
Rule: arrange BGM/SFX after the visual structure is largely locked. Any duration/order change must end with a complete SFX-frame realignment; audiovisual misalignment is a required pre-delivery check.
Case: the user said, “After these changes, readjust the sound-effect positions to match the new timeline.” The whole table was repinned to the new 1085f timeline. The lesson: picture changes 11 hours after initial SFX placement forced complete repinning; two of three repinning rounds were purely knock-on costs of picture revisions.
Self-check: did this round change shot duration/order? If so, was every SFX table entry realigned?

### S4. Foley before decoration: match each visible action with its real sound, and trim audio to the action's exact duration
Rule: give each visible action its corresponding sound (keyboard for typing, individual pops for arrivals); a generic swoosh cannot substitute for a distinctive action. Trim long samples to their visual section (Sequence truncation), matching the action's duration exactly.
Case: the user said, “You can add typing sounds when content appears on the weekly-report page” (the template's weekly-report page). The document reveal received typewriter audio; keyboard.mp3 was trimmed to 24f/44f for two contexts.

Practical points (sound-design §4.1): choose playback windows and gain from actual measurements of the newly downloaded file.
**Set `durationInFrames` explicitly for action samples >5s**; ambient sound follows shot length, while impact reverberation retains its natural tail.
**Quiet assets with peaks <-12dB**: `volume` is a multiplier; even 1.0 may be masked by BGM.
Prefer a different source or preprocessing. If needed, use >1 gain and check peaks in the rendered output; remeasure after processing and update the source record.


Self-check: does each distinctive visual action (typing/clicking/landing) have its own foley? Does an effect keep sounding after its action ends? Can every effect actually be heard in the finished film (is a quiet source loud enough)?

### S5. Correct two audiovisual offsets: measure the output-track offset for each render pipeline and subtract it centrally; measure each source's peak lag separately
Rule: a rendered film's whole audio track has a fixed lag relative to video, originating in output encoding/muxing (AAC encoder priming, typically 2048 samples at 48kHz ≈1.28f@30fps; tracked in remotion-dev/remotion#7099), not `<Audio>`/`Sequence.from` behavior. Measure and record it per pipeline (Remotion version + codec + sample rate + container): extract audio from the finished render, use normalized cross-correlation against 2–3 original sharp SFX, and accept the measurement only when their residuals agree. Subtract compensation centrally in the render-layer from expression, rather than editing individual frame entries. Measure each source's own peak lag (when its peak is not at the file start). The common formula is `from = 目标峰值帧 − 峰值滞后 − 输出偏移` (target peak frame minus peak lag minus output offset). See sound-design §4.6 for method and boundaries: do not lengthen truncation-based effect windows; full compensation is impossible within the first 2f.
Case: AiflPromo measured click lag at 2032 samples and impact at 2066 samples (≈1.27–1.29f), matching the AAC-priming signature; the rendered file's elst did not declare padding removal. The promo-ink era had measured 4f (≈133ms, far above the priming scale, with cause unverified): constants cannot be carried across pipelines. Without compensation, the two offsets combined to delay the strongest hit by 0.27s, visibly out of sync. In a beat-synced film, 2–3 frames can make otherwise sensible beat motion appear to shake without cause (one contributor to user feedback on 2026-08-22).
Self-check: was this pipeline's output-track offset measured, with Remotion version/codec/sample rate/container recorded beside it? Is compensation subtracted centrally in the from expression or scattered among individual frame entries? Was peak lag measured for sources with a clear attack peak?

---

## Copy (C)

### C1. Rewrite copy against the finished shots after picture lock; narrate animation-only sections too
Rule: initial copy is a placeholder. Once visuals are final, rewrite it shot by shot against the film. Add short explanatory captions to animation-only shots; do not leave silent explanatory gaps (except the clean brand finale).
Case: the user said, “Rewrite the copy based on my complete video now. The current words do not seem to match the visuals well, and should the animated parts have some explanation too?” Titles were rewritten and explanatory captions added to the filmed shots.
Self-check: does each line match its image? Is any animation section longer than 3 seconds without explanation?

### C2. Write slogans as “team + product feature name + concrete benefit”; make abstract metaphors specific
Rule: slogans should be concrete and include feature names (Paper Radar / weekly report), avoiding abstract metaphorical language (generic board/place slogans). Put a lead-in title card before an important feature appears.
Case: the user edited the words directly: change 'All your research, one board' to 'All team's research, one place to go'… change 'The morning reading' to 'Paper Radar, tailored for your morning reading'; and “Before the final document-page demonstration, add another text screen” (the template's weekly-report page). Three lines were replaced word by word, and a lead-in title card was added before the document page.
Self-check: does each slogan contain a specific feature name/benefit? Is any sentence sustained only by metaphor?

### C3. Annotations in a 3D shot live in the same 3D space: page-space, shared perspective, angled view, large type and marker highlights
Rule: in-scene annotations for a 3D subject belong in the same 3D space (page coordinates, the same camera perspective, translateZ hovering + shadow). Flat overlaid text disconnects from the scene. Style it with large serif type and marker highlights on keywords.
Case: the user said, “Put the text on the left, larger and more noticeable, with highlight, and make its perspective float in 3D too, filmed at an angle” (after rejecting a flat title-card version). The hero-hover annotation was rebuilt in page-space with an angled perspective and marker highlight.
Self-check: does each text element in a 3D shot move with the scene camera, or is it stuck to the screen glass?

---

## Process (P)

### P1. Render and inspect frame captures yourself before delivery; do not make the user perform the first quality check
Rule: after every revision, render and inspect key-frame screenshots one by one (composition/shake/text sharpness/visible artifacts). Where needed, use pixel-level tools (crop enlargement/two-frame diff) to verify before presenting to the user.
Case: the user's first viewing prompted, “Did you inspect screenshots yourself? The camera angle is poor and there is a small shake I cannot explain.” The pipeline then gained crop/diff/measure self-check scripts and versioned still-frame archives under out/qa/, establishing frame-based review.
Self-check: which frames did I inspect before sharing this version? Is there screenshot evidence for the key shots?

### P2. Break reference footage down frame by frame into techniques, then assess fit shot by shot; do not apply it globally
Rule: when reference footage exists, extract frames and write a motion breakdown (implementation list for each animation/transition/effect) into the spec, choosing by project fit. An image reference describes the feel of a class of shots, not a command for the whole film's style. Check applicability per shot before implementing, and inspect the result before delivery.
Case: the user said, “Extract as many frames as possible from the original video… reproduce and adapt them to our project, without forcing what does not fit.” A motion breakdown in the spec led to successive approvals. Counterexample: three reference images were applied as one global tilted-camera style; the user rejected it with “Not done well… roll back,” and shots were rebuilt individually.
Self-check: does each reference technique have an explicit adopt/discard decision? Has one reference image become a style command for the entire film?

### P3. Resolve ambiguous feedback references first; if the wrong object was changed, cleanly revert the whole commit and redo rather than patching the mistaken version
Rule: for ambiguous feedback such as “the first title,” confirm the intended object before acting. If the change lands on the wrong object, immediately revert the whole commit and start again. Keep each change in an independent commit for a clean rollback.
Case: the user said, “Not the first title card; I mean the animations where AI field lab appears at the beginning and end.” The feedback was first misunderstood and a hold added to card1; the change was cleanly reverted within 8 minutes, then redone on the correct object and approved.
Self-check: am I sure which object this feedback refers to? Is the current commit small enough for a one-step rollback if it is wrong?

### P4. Map a feature list to shots first; each animation technique leads only once in the film, and duplicate shots/information are deleted
Rule: before production, list product features (dashboard/details/papers/weekly report/brand) and map each to a shot. Missing a core feature means rework. Each technique (fly-in/stack/page turn) is the lead only once in the film. Edit by asking “What new information does this shot add?” Each asset/information item appears only once; delete duplicates.
Case: the user said, “Other animations feel too similar; the website's full features are not sufficiently shown,” and “Very good, but where is the weekly-report section?” (the template's weekly-report page), leading to feature shots being added. “The second-last shot repeats the project cards; it can go” led to removal of the duplicate overview and deduplication of the closing slogan.
Self-check: does every feature have a corresponding shot? Do two shots lead with the same technique or say the same thing?
