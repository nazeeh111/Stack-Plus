# slides.md — Presentation Design Specification

> **Purpose**: Drop this file into any project root. An AI agent reading it will generate presentation slides with editorial-grade visual design — distinctive, asymmetric, typographically sophisticated layouts that break from AI-generated sameness. This is not a template. It is a design system specification that produces unique decks with a consistent visual identity.

> **Format**: Inspired by Google Labs' [design.md](https://github.com/nichochar/design.md) — a YAML-structured design token system paired with prose design rationale. Adapted here specifically for presentation slide design.

---

## Design Token System

```yaml
# ──────────────────────────────────────────────────
# SLIDES.MD — DESIGN TOKENS
# ──────────────────────────────────────────────────
# Copy this YAML block into your presentation config
# or reference it as the source of truth for slide design.
# Tokens use the {path.to.token} reference syntax.

meta:
  format: slides.md/1.0
  canvas: 1920x1080  # 16:9 HD standard
  dpi: 150
  export: [pdf, pptx, html]

# ─── P1: COLOR FOUNDATION ───
colors:
  # The 60-25-10-5 allocation model
  dominant-surface: null        # 60% — the ground. User MUST set this.
  secondary-surface: null       # 25% — contrast zones, split backgrounds.
  accent: null                  # 10% — highlight, CTA, data emphasis. ONE job only.
  accent-job: null              # Define: "data-emphasis" | "cta" | "section-marker" | "pull-quote"
  text-primary: null            # Must pass 4.5:1 on dominant-surface
  text-secondary: null          # Muted, for captions/labels. 3:1 minimum.
  text-on-accent: null          # Must pass 4.5:1 on accent
  text-on-secondary: null       # Must pass 4.5:1 on secondary-surface
  
  # Temperature guidance (pick one direction per deck)
  # warm: earth tones, terracotta, blush, amber — signals approachability
  # cool: teal, navy, slate, cyan — signals authority and precision
  # mixed: deliberate warm/cool zone system (e.g., warm content, cool data)
  temperature: null             # "warm" | "cool" | "mixed"
  
  # Hard rules
  max-palette-size: 5           # Dominant + secondary + accent + 2 text colors
  gradients: never              # Flat surfaces only. No gradient backgrounds.
  pure-black: never             # Use near-black (e.g., #18181B, #1A1B21)
  pure-white: never             # Use off-white (e.g., #FAFAF9, #F5F5F4)

# ─── P2: TYPOGRAPHY PAIRING ───
typography:
  display:
    fontFamily: null            # User sets. Carries the deck's personality.
    # Guidance: Serif (Didone, Transitional) = editorial gravitas
    #           Geometric sans = modern tech
    #           Stencil/cutout = bold creativity
    #           Slab serif = confident, grounded
    fontSize-range: 48px–120px
    fontWeight: 700
    lineHeight: 0.95–1.1
    letterSpacing: -0.02em to -0.05em
    textTransform: null         # "uppercase" | "none" | "mixed-case"
    
  subtitle:
    fontFamily: "{typography.display.fontFamily}"
    fontSize: 28px–36px
    fontWeight: 500–600
    lineHeight: 1.2–1.3
    
  body:
    fontFamily: null            # User sets. Clean sans, high x-height.
    fontSize-range: 18px–24px
    fontWeight: 400
    lineHeight: 1.4–1.6
    maxLines: 5                 # Per text block. More = split the slide.
    
  caption:
    fontFamily: "{typography.body.fontFamily}"
    fontSize: 12px–16px
    fontWeight: 400
    lineHeight: 1.3
    color: "{colors.text-secondary}"
    
  hero-metric:
    fontFamily: "{typography.display.fontFamily}"
    fontSize: 72px–120px
    fontWeight: 700–800
    lineHeight: 1.0
    # Used for single standout numbers on data slides
    
  # Type scale ratios (choose one)
  # 1.250 (Major Third) — compact hierarchy, professional
  # 1.333 (Perfect Fourth) — clear separation, editorial
  # 1.414 (Augmented Fourth) — dramatic jumps, bold
  scale-ratio: 1.333
  
  # Signature typographic moves (pick 1–2 per deck)
  signature-moves:
    - null  # Options: "oversized-bleed" | "vertical-rotated" | "stencil-headers"
            #          "mixed-case" | "tight-tracking" | "drop-cap"

# ─── P3: ACCENT JOB DEFINITION ───
accent:
  color: "{colors.accent}"
  job: "{colors.accent-job}"
  # The accent has ONE role. Define it here and enforce it everywhere.
  # "data-emphasis" — accent marks key data points, chart highlights, hero metrics
  # "cta" — accent is for action elements, buttons, links, next-step prompts
  # "section-marker" — accent highlights current section in navigation
  # "pull-quote" — accent decorates quotation marks and quote attribution
  #
  # When the accent does everything, it does nothing. Constraint = identity.
  usage-cap: 3                  # Maximum accent-colored elements per slide

# ─── P4: SIGNATURE MOTIF ───
motif:
  type: null                    # "geometric" | "line-system" | "shape-language" | "decorative"
  
  # Geometric: circles, triangles, rectangles as masks/dividers/framing
  # Line-system: horizontal rules, vertical dividers, connector lines with dot terminators
  # Shape-language: consistent rounded-vs-sharp, organic-vs-angular
  # Decorative: oversized quotation marks, bracket shapes, numbered markers, halftone dots
  
  element: null                 # The specific element. E.g., "circle", "horizontal-line-with-dot-terminals"
  
  rules:
    appears-on-every-slide: true
    varies-per-slide: true      # Enlarged, cropped, rotated, recolored — never identical
    never-competes-with-content: true
    serves-functional-role: true # Masking images, framing sections, connecting items
    
  # Example motif systems observed in high-end decks:
  # - Mondrian-inspired: overlapping colored rectangles + circles at varying scales
  # - Editorial connectors: horizontal lines with dot terminals linking list items
  # - Circle masks: all images cropped to circles, circles also used as backgrounds
  # - Vertical text bars: rotated text running vertically as a structural sidebar

# ─── P5: CHART & DATA TREATMENT ───
charts:
  style: flat                   # No 3D, no gradients on chart elements
  gridlines: faint-or-none      # Very light if present, never dark
  labels: direct                # Labels on data elements, not in separate legends
  accent-data-point: true       # Key data point gets accent color; everything else neutral
  
  tables:
    borders: none-visible       # No cell borders. Use row tinting instead.
    header: tinted              # Header row in accent or secondary color
    rows: alternating-subtle    # Very light alternating row background
    padding: generous           # 12–16px row padding minimum
    font: "{typography.body.fontFamily}"
    header-font: "{typography.display.fontFamily}"
    header-size: "{typography.caption.fontSize}"
    
  hero-metrics:
    size: 72px–120px
    font: "{typography.hero-metric.fontFamily}"
    placement: left-half        # Number fills left, context fills right
    unit-label: below           # Units/labels in caption weight below the number
    
  comparison:
    bias: visual-winner         # Layout argues for one side (size, color, position)
    neutral: only-when-stated   # Explicit opt-in to neutral comparison

# ─── P6: AVOID LIST ───
avoid:
  - centered-everything         # Asymmetry is the default
  - icon-rows                   # 3–5 identical-weight icons in a row
  - gradient-backgrounds        # Flat color, split zone, or image instead
  - drop-shadow-on-text         # Never
  - bullet-list-as-layout       # Use spatial grouping, cards, or columns
  - clip-art                    # No generic stock illustrations
  - more-than-6-elements        # Maximum 6 visual elements per slide
  - decorative-animations       # Static export must be fully legible
  - thank-you-only-closing      # Closing slide needs a CTA or takeaways
  - uniform-card-grid           # Vary sizes, make one card dominant
  - same-layout-3x              # Never repeat a layout pattern 3 consecutive slides
  - placeholder-text            # No lorem ipsum, no "Insert here"
  - rainbow-palettes            # Max 5 colors total
  - medium-weight-everything    # Use weight contrast (400 body, 700 display)
  - slide-transition-effects    # Content, not motion, carries the story

# ─── SPACING & LAYOUT ───
spacing:
  base-unit: 8px
  scale: [4, 8, 16, 24, 32, 48, 64, 96]  # px
  margins:
    top: 48px–64px
    bottom: 48px–64px
    left: 64px–96px
    right: 64px–96px
  gutter: 24px
  negative-space-minimum: 30%  # Of total slide area
  
grid:
  columns: 6                   # 6-column grid allows 2-col and 3-col layouts
  column-width: flexible
  gutter: "{spacing.gutter}"
  
  # Named grid zones for layout reference
  zones:
    left-third: columns 1–2
    center-third: columns 3–4
    right-third: columns 5–6
    left-two-thirds: columns 1–4
    right-two-thirds: columns 3–6
    narrow-left: column 1
    wide-right: columns 2–6

# ─── IMAGE TREATMENT ───
images:
  masks:
    shape: null                 # "circle" | "rounded-rect" | "none" — match motif system
    consistency: all-same       # Every image uses the same mask treatment
  filters:
    consistency: all-same       # All B&W, all color, or all duotone — never mixed
  placement:
    full-bleed: allowed
    overlap: allowed            # Images can overlap each other (collage style)
    edge-tension: encouraged    # Position images near edges, not floating in center
  photography-over-illustration: true  # Real photos > stock illustrations
```

---

## Slide Type Specifications

### Cover Slide

The cover establishes the deck's visual identity in one frame. A stranger seeing this slide should immediately sense the deck's personality.

**Layout strategies** (choose one per deck):

| Strategy | Structure | When to use |
|---|---|---|
| Hero Image + Type Overlay | Full-bleed photo. Title in display face at lower-left or upper-right third. Subtle backing (darkened zone, solid band, or frosted panel). | Photo-driven brands, portfolios, event decks |
| Typographic Monument | No image. Title IS the visual at 80–120pt, breaking across lines with deliberate rag. Motif provides texture. | Conceptual decks, text-forward brands |
| Split Zone | 60/40 or 70/30 vertical split. Image zone + solid color zone with title. Never 50/50. | Corporate, pitch decks |
| Collage Entry | 2–3 overlapping masked images at varying scales. Title weaves between them. | Creative agencies, editorial, culture decks |

**Required elements**: title, subtitle/tagline, presenter name + date (small, bottom edge), logo (small, corner).  
**Forbidden**: centered logo at 50% slide width, gradient overlays, more than one display-size text element.

**Composition example — Collage Entry** (observed in Presentation 2):
```
┌──────────────────────────────────────────────┐
│                                              │
│   ┌─────────┐                                │
│   │  img 1  │  ┌──────────┐                  │
│   │ (large) │  │  img 2   │                  │
│   └─────────┘  │ (medium) │                  │
│                └──────────┘                  │
│                                              │
│   T H E   D E C K   T I T L E              │
│   Subtitle in body face                      │
│                                              │
│   Name · Date                    [logo]      │
└──────────────────────────────────────────────┘
```

---

### Section Divider

Punctuation, not a paragraph. Signals a topic shift with minimal content.

**Layout strategies**:
- Full secondary-color field + section title in display face (large). Motif at increased scale.
- Full-bleed image + section title in contrasting display type, positioned off-center.
- Giant section number (200pt+, light weight) + section name in regular weight beside or below.

**Rules**: display face only. No body text. No descriptions. The divider is a breath, not a lecture.

---

### Content / Body Slide

The workhorse. Vary layout across the deck — never use the same composition 3 consecutive times.

**Layout systems** (alternate across deck):

**1. Asymmetric Two-Column (60/40 or 70/30)**
```
┌──────────────────────────────────────────────┐
│                                              │
│   HEADLINE THAT STATES           ┌────────┐  │
│   THE CONCLUSION                 │        │  │
│                                  │ IMAGE  │  │
│   Body text here, 3–5 lines     │  or    │  │
│   maximum. Each line adds        │ GRAPH  │  │
│   meaning.                       │        │  │
│                                  └────────┘  │
│                                  Caption     │
│                                              │
│   [motif element]                            │
└──────────────────────────────────────────────┘
```

**2. Offset Grid (content in right two-thirds, left third is color/image band)**
```
┌──────────────────────────────────────────────┐
│ ▓▓▓▓▓▓▓▓▓│                                  │
│ ▓ color  ▓│  HEADLINE                        │
│ ▓ band   ▓│                                  │
│ ▓ or     ▓│  Content block 1                 │
│ ▓ image  ▓│  Content block 2                 │
│ ▓ strip  ▓│  Content block 3                 │
│ ▓▓▓▓▓▓▓▓▓│                                  │
└──────────────────────────────────────────────┘
```

**3. Magazine Spread (text wraps around images, pull quote breaks column)**
```
┌──────────────────────────────────────────────┐
│                                              │
│   HEADLINE                                   │
│                                              │
│   Text text text    ┌──────┐  text text      │
│   text text text    │ img  │  text text      │
│   text text text    └──────┘  text text      │
│                                              │
│   ╔══════════════════════╗                   │
│   ║ "Pull quote in       ║                   │
│   ║  display italic"     ║                   │
│   ╚══════════════════════╝                   │
└──────────────────────────────────────────────┘
```

**4. Full Bleed + Caption Bar**
```
┌──────────────────────────────────────────────┐
│                                              │
│         [FULL BLEED IMAGE]                   │
│                                              │
│                                              │
│                                              │
├──────────────────────────────────────────────┤
│  Title · Body text · Caption     [motif]     │
└──────────────────────────────────────────────┘
```

**5. Card Cluster (2–3 cards at different sizes on Rule of Thirds grid)**
```
┌──────────────────────────────────────────────┐
│                                              │
│   HEADLINE                                   │
│                                              │
│   ┌────────────────┐   ┌──────────┐          │
│   │                │   │          │          │
│   │  LARGE CARD    │   │  SMALL   │          │
│   │  (dominant)    │   │  CARD    │          │
│   │                │   └──────────┘          │
│   └────────────────┘   ┌──────────┐          │
│                        │  SMALL   │          │
│                        │  CARD    │          │
│                        └──────────┘          │
└──────────────────────────────────────────────┘
```

**Content rules**:
- Headlines state the conclusion: "Revenue grew 34% YoY" not "Revenue Overview"
- Body text: 3–5 lines maximum
- Maximum 6 visual elements per slide
- One idea per slide — two concepts = two slides

---

### Data / Chart Slide

Data slides argue a point. They do not neutrally display numbers.

**Layout strategies**:

| Strategy | Structure |
|---|---|
| Hero Metric + Context | One number at 72–96pt fills left half. Chart or supporting text on right. The number IS the headline. |
| Chart + Annotation | Chart at 60% of slide. Key points called out with leader lines or direct labels. No separate legend. |
| Comparison Strip | 2–3 side-by-side metrics, each with number + label + sparkline. Accent marks the winner. |
| Table as Design | Tinted header row, no vertical rules, generous padding, alternating row tints. |

**Rules**:
- Never show a chart without interpreting it — the headline or annotation tells the audience what to see
- Accent color marks the key data point only; everything else is neutral
- Hero metrics use display face at 72pt+, supporting numbers use body face
- Units and labels in caption weight below the number

---

### Team / People Slide

Where decks most often look generic. Break the uniform headshot grid.

**Layout strategies**:

| Strategy | Description |
|---|---|
| Offset Gallery | Photos at varying sizes, same mask shape. Lead person is visually largest. |
| Magazine Roster | Horizontal strips per person — photo left, name + role + bio right, separated by hairline rules. |
| Hero + Supporting | Primary person large with photo + bio. Others in compact row below. |
| Collage | Overlapping headshot crops with positioned name labels. Background color bands behind groups. |

**Rules**: all photos use the same treatment (mask shape, filter, border). Consistency signals design intention.

---

### Quote Slide

A typography exercise. Let the words carry the slide.

**Layout strategies**:
- **Pull Quote**: quote in display face at 32–48pt. Oversized decorative quotation marks (motif variant). Attribution in body face, subdued color.
- **Image + Quote Split**: speaker photo 40%, quote text 60%. Quote in distinct face (italic or display serif).
- **Full Color + Quote**: solid accent or secondary color field. Quote in white/contrasting display type. The quote is the only element.

**Rules**: no text boxes with visible borders. Quotes breathe in open space. Never put a quote inside a card or container.

---

### Timeline / Process Slide

Sequential information needs a clear spatial reading path.

**Layout strategies**:

| Strategy | Description |
|---|---|
| Horizontal Track | Thin horizontal line with motif nodes at each step. Labels above, details below. Current step in accent. |
| Vertical Bars | Each period is a vertical colored bar. Varying height encodes magnitude. Labels at top. |
| Staggered Cards | Steps as cards in a downward-stepping diagonal, connected by the line system motif. |
| Column Flow | 3–5 columns per phase, connected by narrow motif elements (arrows, lines). |

**Rules**: read left-to-right or top-to-bottom. Never circular — circular timelines confuse reading order.

---

### Comparison Slide

Visual persuasion. The layout argues.

**Layout strategies**:
- **Split Screen**: hard vertical or diagonal divide. Each side gets its own color temperature. Preferred option gets 55% of the space.
- **Table Comparison**: styled table with winner column highlighted in accent.
- **Overlay**: both options shown but one is dominant (larger, colored, foreground) while the other is recessive (smaller, gray, background).

**Rules**: comparisons are never visually neutral unless explicitly stated. Slides are persuasion tools — the layout takes a side.

---

### Summary / Closing Slide

More than "Thank You." The last frame the audience sees must drive action.

**Layout strategies**:
- **Key Takeaways + CTA**: 3 takeaway statements in display face, stacked with generous spacing. Clear next step below (contact, URL, QR code).
- **Typographic Echo**: mirrors cover layout with closing content. Creates bookend symmetry.
- **Image + Message**: strong closing image with a single statement in display face.
- **Contact Card**: designed as a visual business card — name, role, contact, QR, arranged asymmetrically.

**Rules**: must include a concrete next step. "Questions?" is not a next step.

---

## Compositional Principles

These apply to EVERY slide regardless of type.

### 1. Rule of Thirds
Divide the slide into a 3x3 grid. Place the primary content at an intersection point, not in the center. Centers are for symmetry-by-design (rare), not by default.

### 2. Asymmetric Balance
Balance through visual weight, not mirroring. A large image left is balanced by text + motif right. A heavy color field top is balanced by white space bottom. Equal halves signal indecision.

### 3. Negative Space as Content
Empty space is designed, not leftover. Minimum 30% of every slide is breathing room. Crowded slides = unedited content. Space isolates important elements and creates hierarchy.

### 4. Single Entry Point
Every slide has ONE element the eye hits first — largest, brightest, or highest-contrast. Design it deliberately. If everything is the same weight, the slide has no voice.

### 5. Guided Reading Path
After the entry point, the eye follows: entry point → supporting content → detail. Use size, position, and color to guide this. The path never loops or branches.

### 6. Edge Tension
Elements near edges create dynamism. Elements bleeding off edges create expansiveness. Elements centered create stasis. Use all three intentionally, defaulting to edge tension.

### 7. Contrast Stacking
The most important element gets multiple contrast types layered (size + color + weight). Supporting elements get one. Background elements get none.

### 8. Pattern Interruption
After 2–3 slides of consistent layout, introduce a deliberate break — a full-bleed image, a different grid, a color-field slide. This is the Von Restorff effect: the different thing is remembered.

### 9. Pacing Rhythm
A deck is a sequence, not a collection. Alternate between dense and sparse slides. Follow a text-heavy slide with a visual-dominant one. Follow detailed content with a breathing-room divider.

### 10. Gestalt Grouping
Elements that belong together must be visibly closer to each other than to unrelated elements. Proximity is meaning — if padding-within equals margin-between, grouping collapses.

---

## Anti-Pattern Detection

When generating or reviewing slides, detect and correct these failures:

| Anti-Pattern | Detection Signal | Fix |
|---|---|---|
| Everything centered | All elements share the same horizontal center | Push primary content to a thirds intersection |
| Uniform card grid | 3+ cards of identical size in a row | Vary sizes, make one dominant |
| Title + bullet list | `# Title` followed by `- item` list | Convert to spatial layout with grouped elements or columns |
| Decorative icon row | 3–5 icons of equal visual weight in a line | Remove, or make one icon large and meaningful |
| Gradient background | Any gradient used as a surface | Flat color, split zone, or image |
| Wall of text | >5 lines of body text | Split into 2 slides, or cut to key points |
| No visual hierarchy | All elements same size/weight/color | Make one element 2–3x larger |
| Stock photo + centered text | Generic photo with overlaid centered title | Mask the photo, offset the text, add the motif |
| Rainbow palette | >5 distinct hue families in use | Reduce to dominant + secondary + accent |
| Layout repetition | Same composition on 3+ consecutive slides | Alternate between layout systems |
| Missing motif | Slide has no instance of the signature visual element | Add a variant of the motif (scaled, cropped, rotated) |
| Neutral comparison | Two options presented with equal visual weight | Make the preferred option visually dominant |

---

## Design System Generation Protocol

When an AI agent reads this file to generate a presentation, it should follow this sequence:

### Step 1: Establish the 6 Parameters
Based on the presentation topic, audience, and tone, define:
1. Color Foundation — dominant, secondary, accent, temperature
2. Typography Pairing — display face, body face, scale ratio
3. Accent Job — what the accent color does (one thing only)
4. Signature Motif — the recurring visual element
5. Chart Treatment — how data is styled
6. Avoid List — confirm the defaults, add topic-specific bans

### Step 2: Design the Cover
The cover is designed first because it establishes the visual vocabulary. Every subsequent slide inherits from it.

### Step 3: Compose Slide-by-Slide
For each slide:
1. Determine slide type (content, data, team, quote, etc.)
2. Choose a layout strategy from the type's options — ensuring no 3-consecutive repeats
3. Apply the compositional principles (Rule of Thirds, asymmetric balance, edge tension)
4. Verify against the Avoid List
5. Run the Craft Checklist (below)

### Step 4: Verify Deck Flow
Review the full sequence for:
- Pacing rhythm (dense/sparse alternation)
- Layout variety (no 3-consecutive same layouts)
- Motif continuity (appears on every slide, varied)
- Color consistency (accent used for its assigned job only)
- Pattern interruption (at least one visual break every 4–5 slides)

---

## The Craft Checklist

Run this on every slide before finalizing:

- [ ] ONE clear entry point?
- [ ] Asymmetric layout (not centered-everything)?
- [ ] Headline states a conclusion, not a topic?
- [ ] Body text under 5 lines?
- [ ] 6 or fewer visual elements?
- [ ] Signature motif appears (varied, not identical to previous slide)?
- [ ] At least 30% negative space?
- [ ] Color follows the hierarchy (dominant/secondary/accent)?
- [ ] Recognizable as part of THIS deck if seen alone?
- [ ] Layout differs from the previous slide?
- [ ] Text passes contrast requirements (4.5:1)?
- [ ] No items from the Avoid List present?

---

## Example Design Systems

Three complete parameter sets derived from analyzed high-end presentation decks:

### Example A: "Mondrian Tech" (geometric + authoritative)
```yaml
colors:
  dominant-surface: "#F5F0EB"    # Warm off-white
  secondary-surface: "#1A1B21"   # Near-black
  accent: "#E94E77"              # Coral pink
  accent-job: data-emphasis
  temperature: mixed             # Warm surfaces, cool secondary
typography:
  display: "Playfair Display"    # Didone serif
  body: "Inter"                  # Clean geometric sans
  scale-ratio: 1.333
  signature-moves: ["tight-tracking"]
motif:
  type: geometric
  element: "overlapping-rectangles-and-circles"
charts:
  style: flat
  accent-data-point: true
```

### Example B: "Editorial Warmth" (fashion-editorial + approachable)
```yaml
colors:
  dominant-surface: "#E8E0D8"    # Cream
  secondary-surface: "#C4A88C"   # Taupe
  accent: "#A0654B"              # Terracotta
  accent-job: pull-quote
  temperature: warm
typography:
  display: "Libre Baskerville"   # Transitional serif
  body: "Source Sans Pro"        # Humanist sans
  scale-ratio: 1.414
  signature-moves: ["vertical-rotated", "stencil-headers"]
motif:
  type: line-system
  element: "horizontal-lines-with-dot-terminals"
charts:
  style: flat
  tables:
    header: tinted-terracotta
```

### Example C: "Deep Studio" (photography-portfolio + bold)
```yaml
colors:
  dominant-surface: "#1B4B4B"    # Deep teal
  secondary-surface: "#F5F0EB"   # Cream (for contrast slides)
  accent: "#C8A951"              # Olive gold
  accent-job: section-marker
  temperature: cool
typography:
  display: "Archivo Black"       # Bold geometric sans
  body: "Work Sans"              # Clean sans
  scale-ratio: 1.250
  signature-moves: ["oversized-bleed"]
motif:
  type: geometric
  element: "circle-masks"
images:
  masks:
    shape: circle
  filters:
    consistency: all-color
charts:
  style: flat
  hero-metrics:
    size: 96px
```

---

## Marp CSS Integration

When generating slides as Marp markdown, translate design tokens into CSS custom properties:

```css
/* Auto-generated from slides.md design tokens */
:root {
  /* Colors */
  --color-dominant: var(--slides-dominant-surface);
  --color-secondary: var(--slides-secondary-surface);
  --color-accent: var(--slides-accent);
  --color-text: var(--slides-text-primary);
  --color-text-muted: var(--slides-text-secondary);
  
  /* Typography */
  --font-display: var(--slides-display-family);
  --font-body: var(--slides-body-family);
  --size-display: clamp(48px, 6vw, 120px);
  --size-subtitle: clamp(28px, 3vw, 36px);
  --size-body: clamp(18px, 2vw, 24px);
  --size-caption: clamp(12px, 1.5vw, 16px);
  
  /* Spacing */
  --space-unit: 8px;
  --margin-slide: 64px;
  --gutter: 24px;
}

section {
  background: var(--color-dominant);
  color: var(--color-text);
  font-family: var(--font-body);
  padding: var(--margin-slide);
}

section h1, section h2 {
  font-family: var(--font-display);
  letter-spacing: -0.02em;
  line-height: 1.05;
}

/* Layout utility classes */
section.split-60-40 { /* Asymmetric two-column */ }
section.offset-grid { /* Left color band + right content */ }
section.full-bleed { padding: 0; }
section.section-divider {
  background: var(--color-secondary);
  color: var(--color-text-on-secondary);
  display: flex;
  align-items: center;
}
```

---

## Tool-Agnostic Application

This specification is designed to work with any presentation tool:

| Tool | How to apply slides.md |
|---|---|
| **Marp** | Convert tokens to CSS custom properties. Use Marp directives for per-slide class assignment. |
| **Gamma.app** | Use tokens as design system input. Apply layout strategies as card arrangement guidance. |
| **Google Slides / PowerPoint** | Convert tokens to slide master theme. Implement layouts as master slide templates. |
| **Figma / Figma Slides** | Convert tokens to Figma variables. Build layouts as component variants. |
| **HTML/CSS** | Direct CSS implementation with tokens as custom properties. |
| **Reveal.js** | Convert to Reveal.js theme CSS. Use fragment and layout plugins. |
| **Canva** | Apply as brand kit settings. Use layout strategies as manual composition guidance. |

---

## Version History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-09-12 | Initial specification. Derived from analysis of 37 slides across 3 high-end presentation PDFs, 15 visual design principles from editorial/magazine design research, Marp ecosystem documentation, Google Labs design.md specification, and cognitive load research from peer-reviewed literature. |
