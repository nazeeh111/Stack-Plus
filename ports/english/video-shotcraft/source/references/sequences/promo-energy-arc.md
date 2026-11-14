---
name: promo-energy-arc
一句话: Whole-film energy structure: quiet brand opening → establish one hero → rising feature section spaced by breathing title cards → launch-event peak finale
适用: Default whole-film structure for a 30–60s multi-feature web product promo (fill the structure at storyboard time before choosing cards)
段数: 4 sections + 2–4 breathing title cards
---

## Intent

Combine the pacing rules scattered across R1–R3/Q5/Q8/P4 into one whole-film
curve that can be filled in directly. The finished template film (1085f) and
two independent reproductions (900f each) all converged on the same structure.
It is a default, not a command: a project may deliberately depart from it;
record the departure in the project spec.

## Section table

| Section | Share of duration | Energy | Job | Candidate recipe cards |
|------|----------|------|------|------------|
| ① Brand opening | 8–12% (30s film); opening + hero introduction may total 20% (template film) | Low | Imprint the wordmark + hold ≥1s (R1), then hand over to the product page | brand-ink-open |
| ② Establish one hero | 12–15% | Medium (highest material quality, slowest pacing) | One hero, one complete action arc ≥3s (Q5/R3), establishing the product's atomic unit | spotlight-hero-card (+aesthetic-rules.md Q2 high-resolution rasterize technique) |
| ③ Rising feature section | 55–65% | Alternating medium-high ⇄ low | Tie each shot to a distinct feature; let each technique be the lead only once (P4); insert breathing title cards between shots as needed | deck-deal-flyin / type-and-filter / list-stack-press / row-embed / document-typewriter-reveal |
| ④ Launch-event finale | 13–16% | Peak (highest in the film) | A representative element from each shown feature gathers around the wordmark for a group photo (Q8); sign-off hold ≥1s (R1) | outro-group-photo-launch |

Breathing title-card (paper-title-card) rule: insert one after every 1–2 feature
shots, 50–55f each (≈1.8s), with 2–4 cards in the film. Use one as a lead-in before
an important feature appears (C2). Four of the template film's 10 shots were title
cards; the two reproductions used two each. Choose density by feature-shot count.

## Fill-in procedure (replaces ad-hoc derivation)

1. List the product features (P4) and count the feature shots, N.
2. Allocate the total frames using the section table: first reserve the budgets
   for ①②④ and the title cards, then divide the remainder equally among ③.
   Within each shot budget, **reserve hold/rest frames first** (R1: settled hold
   ≥30f; batch-entry ending 15f; R3), then schedule motion. Do not schedule all
   motion first and look for leftover gaps.
3. Alternate energy within ③: interleave high-energy shots (dealing/stacking) with
   steady-paced shots (interaction/reading fields). Put the densest information
   shot (document/report) before the peak finale. The template and both
   reproductions placed document/report shots in the second- or third-last slot.
4. Scan shots/ frontmatter slot by slot to choose cards; read selected cards fully.
5. Once shots are placed, choose a transition at each join (the three-way choice
   in the shot-transitions technique card) and record it in the storyboard's
   “key motion” column. Deduct transition frames from the adjacent shot budgets.

## Known pitfalls

- Treating the structure as a global style command: the section percentages are
  evidence from one template case (label: single-case precedent). For a 15s film
  or a single-feature product, freely merge sections, but do not omit the opening
  ① hold or the finale ④ peak.
- Filling ③ with high-energy shots only: uninterrupted high energy reads as noise.
  The alternation and title cards are the rhythm itself.
- Writing breathing cards as a second tagline: delete a title card if its copy
  repeats the outro (P4 precedent: deduplicate the outro tagline).

## Reference implementation

template/src/aifl/Main.tsx AIFL_SHOTS section table (sum=1085f).
