# Presentation Design Skill for Claude Code

A Claude Code skill and design specification that generates editorially-crafted presentation slides — distinctive, asymmetric, typographically sophisticated layouts that break from AI-generated sameness.

## The Problem

All AI-generated slides today look the same: centered text, stock gradients, uniform card grids, predictable icon rows, safe sans-serif, even spacing. They're recognizably "AI-made" and lack the intentional, editorial quality that makes presentations memorable.

## What This Solves

This skill teaches Claude Code to design slides like a presentation art director — by applying principles reverse-engineered from award-winning decks, magazine editorial layouts, and visual identity systems. Instead of averaging existing templates, it generates novel compositions with:

- **Distinctive visual identity** via 6 Presentation Parameters (Color Foundation, Typography Pairing, Accent Job, Signature Motif, Chart Treatment, Avoid List)
- **Editorial-grade layouts** with asymmetric compositions, Rule of Thirds placement, and deliberate negative space
- **Per-slide-type strategies** for 9 slide types (cover, section divider, content, data, team, quote, timeline, comparison, closing)
- **Anti-pattern detection** that catches and fixes common AI slide failures (centered-everything, icon rows, bullet-list-as-layout, uniform grids)
- **A craft checklist** run on every slide before finalizing

## What's Included

| File | Purpose |
|---|---|
| `skill/SKILL.md` | Claude Code skill file — teaches AI to act as a presentation art director |
| `slides.md` | Self-sufficient design spec — drop into any project root for AI-generated slides |

### `skill/SKILL.md` — The Skill

The skill file that Claude Code loads when you invoke `/presentation-design`. Contains the full design methodology: 6 Parameters, 9 slide type compositions, 7 compositional principles, anti-pattern table, and the craft checklist.

### `slides.md` — The Design Spec

A portable, tool-agnostic design specification inspired by [Google Labs' design.md](https://github.com/nichochar/design.md). Contains YAML design tokens, layout diagrams, 3 complete example design systems, a 4-step generation protocol, Marp CSS integration, and application guides for Gamma, Google Slides, PowerPoint, Figma, Reveal.js, and Canva.

Drop `slides.md` into any project root. Any AI agent reading it will have everything it needs to generate slides with editorial-grade design.

---

## Installation

### Option 1: Install as a Claude Code Skill (recommended)

```bash
# Clone the repo
git clone https://github.com/blisse-code/presentation-design-skill.git

# Symlink the skill into your Claude Code skills directory
ln -s "$(pwd)/presentation-design-skill/skill" ~/.claude/skills/presentation-design
```

After symlinking, the skill appears in Claude Code and can be invoked with `/presentation-design`.

### Option 2: Install via `npx skills` (if supported)

```bash
npx skills add blisse-code/presentation-design-skill
```

### Option 3: Manual Copy

```bash
# Copy the skill file
mkdir -p ~/.claude/skills/presentation-design
cp skill/SKILL.md ~/.claude/skills/presentation-design/SKILL.md
```

### Option 4: Use `slides.md` Standalone

Just copy `slides.md` into any project root. Any AI tool (Claude, GPT, Gemini, Copilot) can read it and use it as a design specification for generating presentations — no Claude Code skill installation required.

```bash
cp slides.md /path/to/your/project/slides.md
```

---

## Usage

### With Claude Code (skill installed)

Ask Claude Code to create a presentation and it will automatically use the skill:

```
Create a 12-slide pitch deck for a fintech startup targeting enterprise clients.
```

Or invoke the skill directly:

```
/presentation-design
```

The skill will:
1. Establish the 6 Presentation Parameters based on your topic and audience
2. Design the cover slide first (sets the visual vocabulary)
3. Compose each slide using varied layout strategies
4. Verify each slide against the craft checklist
5. Review deck flow for pacing, variety, and motif continuity

### With `slides.md` (any AI tool)

Include `slides.md` in your prompt context and ask the AI to generate slides following its specification:

```
Using the slides.md design spec in this project, create a 10-slide product launch deck.
Use the "Editorial Warmth" example design system as a starting point.
```

### With Marp

The spec includes a Marp CSS integration section. Generate your slides as Marp markdown and the design tokens translate to CSS custom properties:

```bash
# Convert to PDF
npx @marp-team/marp-cli your-deck.md --pdf

# Convert to PPTX
npx @marp-team/marp-cli your-deck.md --pptx
```

---

## Design Philosophy

This skill is built on three convictions:

1. **Slides are editorial design, not information containers.** A slide is closer to a magazine spread than a document page. It should have a point of view, a visual rhythm, and intentional composition.

2. **Constraint creates identity.** A deck with one accent color used for one purpose is more distinctive than a deck with five colors used interchangeably. The 6 Parameters are constraints that force consistency and character.

3. **Asymmetry is the default.** Centered layouts signal that no design decision was made. Asymmetric balance — achieved through visual weight, not mirroring — is how editorial designers create energy and hierarchy.

---

## Research Sources

This skill was developed by analyzing:
- 37 slides across 3 high-end presentation PDFs (Mondrian-geometric, editorial-fashion, photography-portfolio aesthetics)
- 15 visual design principles from editorial and magazine layout research
- Google Labs' [design.md](https://github.com/nichochar/design.md) specification format
- Marp ecosystem documentation and theming system
- Peer-reviewed cognitive load research for presentation design (PMC)
- 2026 design trends (editorial minimalism, retrofuturism, asymmetric grids)
- 40+ sources spanning graphic design theory, attention psychology, and presentation-specific guidance

---

## License

MIT
