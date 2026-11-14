---
name: infographic-creator
description: Create polished infographics from supplied text. Use when the user requests an infographic.
---

An infographic turns data, information and knowledge into a perceptible visual language. It combines visual design with data visualization, compressing complex information into intuitive symbols so audiences can quickly understand and remember the main points.

`Infographic = Information Structure + Visual Expression`

This task uses [AntV Infographic](https://infographic.antv.vision/) to create visual infographics.

Before starting, understand the AntV Infographic syntax specification, including its template list, data structures and themes.

## Language Lock

- The language of these instructions and examples does not determine the final output language.
- If the user writes in English, generated `title`, `desc`, `label` and other copy must remain English; do not automatically translate it into Chinese.
- If the user writes in Chinese, generated `title`, `desc`, `label` and other copy must remain Chinese; do not automatically translate it into English.

## Specification

### AntV Infographic syntax

AntV Infographic syntax is a custom DSL describing infographic rendering configuration. It expresses structure through indentation and supports direct AI generation and streaming output. Its core information includes:

1. template: express the information structure through a template.
2. data: infographic data, including `title`, `desc` and the main data field.
3. theme: theme configuration, including `palette`, fonts and stylization.

For example:

```infographic
infographic list-row-horizontal-icon-arrow
data
  title Title
  desc Description
  lists
    - label Label
      value 12.5
      desc Explanation
      icon document text
theme
  palette #3b82f6 #8b5cf6 #f97316
```

### Mandatory syntax rules

- The first line must be `infographic <template-name>`.
- The template list contains template names alone; actual output must explicitly include the `infographic` prefix on the first line.
- Use `data` / `theme` blocks, with consistent two-space indentation within them.
- Key/value pairs use `键 空格 值` (key SPACE value); object-array entries begin with `-`.
- `icon` may use an exact icon ID, such as `mingcute/server-line`, or a semantic keyword phrase, such as `star fill`.
- Separate words in a semantic keyword phrase with spaces, not hyphens: write `rocket launch`, not `rocket-launch`.
- Add `icon` by default to semantic items in `lists`, `sequences`, `nodes`, `items` and under `compares`/`children`; do not omit it merely because the field is optional.
- If the template name or visual style clearly depends on icons, every main data item should include `icon`.
- If the exact icon ID is uncertain, prefer a concise semantic keyword such as `rocket`, `shield`, `database`, `users` or `chart line` rather than omitting `icon`.
- Omit `icon` only for purely chart-based data points, purely numeric sequences, or an explicitly requested minimal text version.
- Use plain numbers for `value` where possible; put units in `label` or `desc` in preference.
- Prefer the simple inline-array form for `palette`, such as `palette #4f46e5 #06b6d4 #10b981`.
- Colors in `palette` are bare values, without quotes or commas.
- Put only one template-matching main data field in `data`; avoid mixing `lists`, `sequences`, `compares`, `values`, `root` and `nodes`.

Main-data-field selection rules:

- `list-*` → `lists`
- `sequence-*` → `sequences`, with optional `order asc|desc`
- `sequence-interaction-*` → `sequences` + `relations`
  - `sequences` is the list of swimlanes
  - Each swimlane must contain `label`
  - Each swimlane's `children` is its node list
  - Each item under `children` must be an object entry containing `label`
  - Nodes may include `id`, `icon`, `step`, `desc` and `value`
  - `step` represents the time level; items with the same `step` sit at the same height
- `compare-*` → `compares`
  - `compare-binary-*` / `compare-hierarchy-left-right-*`
    - The first level of `compares` must contain exactly two root nodes, one for each side
    - Both root nodes should contain `children`
    - Put the actual comparison items under each side's `children`
    - Each item under `children` must be an object entry containing `label`
    - Even if a side has only 1 metric, represent it as 1 object entry inside `children`
  - `compare-swot`
    - `compares` may directly contain multiple root nodes
    - Each root node may have `children`
  - `compare-quadrant-*`
    - Put the 4 quadrant root nodes directly in `compares`
- `hierarchy-structure` → `items`
- `hierarchy-*` → one `root`, recursively nested through `children`
- `relation-*` → `nodes` + `relations`
  - Simple relationships may also use arrow syntax directly
- `chart-*` → `values`
  - `chart-line-plain-text` / `chart-bar-plain-text` / `chart-column-simple` all use one ordered `values` sequence
  - Each data point uses `label` for its category and `value` for its number
  - The entry order in `values` expresses the line-chart order
- Use `items` as a fallback only when the structure cannot be determined clearly

Theme rules:

- `theme` customizes the theme, such as `palette`, `base` and `stylize`
- Specify a font with `theme.base.text.font-family`, such as `851tegakizatsu`
- Use `theme.stylize` to choose a built-in style and pass parameters
  - `rough`: hand-drawn effect
  - `pattern`: pattern fill
  - `linear-gradient` / `radial-gradient`: gradient styles
- Output only Infographic syntax, without JSON, explanatory text or extra Markdown paragraphs

## Data syntax examples

Concise but complete valid examples by template category:

- `list-*` templates

```infographic
infographic list-grid-badge-card
data
  title Feature List
  lists
    - label Fast
      icon flash fast
    - label Secure
      icon shield check
```

- `sequence-*` templates

```infographic
infographic sequence-ascending-steps
data
  title 发布流程
  sequences
    - label 需求确认
      icon clipboard check
    - label 开发实现
      icon code
    - label 发布上线
      icon rocket
  order asc
```

- `sequence-interaction-*` templates

```infographic
infographic sequence-interaction-compact-animated-badge-card
data
  title 登录校验流程
  sequences
    - label 用户
      icon user
      children
        - label 发起登录
          id user-login
          step 0
          icon login
        - label 收到结果
          id user-result
          step 2
          icon inbox check
    - label 服务端
      icon server
      children
        - label 校验凭证
          id server-verify
          step 1
          icon shield check
        - label 返回结果
          id server-return
          step 2
          icon send
  relations
    user-login - 提交账号密码 -> server-verify
    server-verify - 生成结果 -> server-return
    server-return - 返回结果 -> user-result
```

- `hierarchy-*` templates

```infographic
infographic hierarchy-tree-curved-line-rounded-rect-node
data
  title 组织结构
  root
    label 公司
    children
      - label 产品部
      - label 技术部
```

- `compare-swot` template

```infographic
infographic compare-swot
data
  title 产品 SWOT
  compares
    - label Strengths
      icon trophy
      children
        - label 品牌认知高
          icon star
    - label Weaknesses
      icon alert circle
      children
        - label 成本压力大
          icon wallet
```

- `compare-binary-*` templates

```infographic
infographic compare-binary-horizontal-simple-fold
data
  title 餐桌价格对比
  compares
    - label 原价
      icon tag
      children
        - label 原价
          value 500
          icon tag
    - label 实际支付
      icon wallet
      children
        - label 实际支付
          value 450
          icon check bold
```

- `compare-quadrant-*` templates

```infographic
infographic compare-quadrant-quarter-simple-card
data
  title 任务优先级
  compares
    - label 高价值低成本
    - label 高价值高成本
    - label 低价值低成本
    - label 低价值高成本
```

- `chart-line-plain-text` template

```infographic
infographic chart-line-plain-text
data
  title 模型 A 准确率变化
  desc 第 4 周提升最明显
  values
    - label Week1
      value 86.5
    - label Week2
      value 87.3
    - label Week3
      value 89.1
    - label Week4
      value 91.2
theme
  palette #4f46e5 #db2777 #14b8a6
```

- `relation-*` templates

```infographic
infographic relation-dagre-flow-tb-simple-circle-node
data
  title 系统关系
  nodes
    - label API
    - id db
      label DB
  relations
    API - 读写 -> db
```

- Fallback `items` example

```infographic
infographic list-row-horizontal-icon-arrow
data
  title 要点总结
  items
    - label 效率优先
      desc 聚焦关键动作
    - label 结果导向
      desc 输出可执行结论
```

### Available templates

- chart-bar-plain-text
- chart-column-simple
- chart-line-plain-text
- chart-pie-compact-card
- chart-pie-donut-pill-badge
- chart-pie-donut-plain-text
- chart-pie-plain-text
- chart-wordcloud
- compare-binary-horizontal-badge-card-arrow
- compare-binary-horizontal-simple-fold
- compare-binary-horizontal-underline-text-vs
- compare-hierarchy-left-right-circle-node-pill-badge
- compare-quadrant-quarter-circular
- compare-quadrant-quarter-simple-card
- compare-swot
- hierarchy-mindmap-branch-gradient-capsule-item
- hierarchy-mindmap-level-gradient-compact-card
- hierarchy-structure
- hierarchy-tree-curved-line-rounded-rect-node
- hierarchy-tree-tech-style-badge-card
- hierarchy-tree-tech-style-capsule-item
- list-column-done-list
- list-column-simple-vertical-arrow
- list-column-vertical-icon-arrow
- list-grid-badge-card
- list-grid-candy-card-lite
- list-grid-ribbon-card
- list-row-horizontal-icon-arrow
- list-sector-plain-text
- list-waterfall-badge-card
- list-waterfall-compact-card
- list-zigzag-down-compact-card
- list-zigzag-down-simple
- list-zigzag-up-compact-card
- list-zigzag-up-simple
- relation-dagre-flow-tb-animated-badge-card
- relation-dagre-flow-tb-animated-simple-circle-node
- relation-dagre-flow-tb-badge-card
- relation-dagre-flow-tb-simple-circle-node
- sequence-ascending-stairs-3d-underline-text
- sequence-ascending-steps
- sequence-circular-simple
- sequence-color-snake-steps-horizontal-icon-line
- sequence-cylinders-3d-simple
- sequence-filter-mesh-simple
- sequence-funnel-simple
- sequence-horizontal-zigzag-underline-text
- sequence-mountain-underline-text
- sequence-pyramid-simple
- sequence-roadmap-vertical-plain-text
- sequence-roadmap-vertical-simple
- sequence-snake-steps-compact-card
- sequence-snake-steps-simple
- sequence-snake-steps-underline-text
- sequence-stairs-front-compact-card
- sequence-stairs-front-pill-badge
- sequence-timeline-rounded-rect-node
- sequence-timeline-simple
- sequence-zigzag-pucks-3d-simple
- sequence-zigzag-steps-underline-text
- sequence-interaction-default-badge-card
- sequence-interaction-default-animated-badge-card
- sequence-interaction-default-compact-card
- sequence-interaction-default-capsule-item
- sequence-interaction-default-rounded-rect-node

## Template-selection guidance

- Strict order, step progression or stage evolution → `sequence-*`
- Interaction among multiple roles or systems → `sequence-interaction-*`
- Parallel key points → `list-row-*` / `list-column-*` / `list-grid-*`
- Two-sided, option or before/after comparison → `compare-binary-*`
  - First identify the two sides
  - Then expand `children` for each side
- SWOT analysis → `compare-swot`
- Quadrant analysis → `compare-quadrant-*`
- Hierarchical tree → `hierarchy-tree-*`
- Statistical trend or change in one sequence → `chart-line-plain-text`
- Statistical comparison or comparison within one numeric group → `chart-bar-plain-text` / `chart-column-simple`
- Node relationships or process dependencies → `relation-*`
- Word-frequency topics → `chart-wordcloud`
- Mind map → `hierarchy-mindmap-*`

### Complete output example

```infographic
infographic list-row-horizontal-icon-arrow
data
  title 产品增长要点
  desc 聚焦获客、转化、复购三个阶段
  lists
    - label 获客
      desc 多渠道投放与内容触达
      icon rocket launch
    - label 转化
      desc 优化路径并减少流失
      icon chart line
    - label 复购
      desc 会员权益与分层运营
      icon repeat
theme
  palette #3b82f6 #8b5cf6 #f97316
```

## Output format

Output just one `plain` code block, without any explanatory text:

```infographic
infographic list-row-horizontal-icon-arrow
data
  title 标题
  desc 描述
  lists
    - label 条目
      value 12.5
      desc 说明
      icon document text
theme
  palette #3b82f6 #8b5cf6 #f97316
```

## Self-check list

Before output, check:

- The first line is `infographic <template-name>`
- Only one main data field is used, and it matches the template
- Main data items have appropriate `icon` values, especially lists, steps, nodes, comparisons and templates with `icon` in their name
- `palette` contains bare color values without quotes or commas
- Swimlane nodes in `sequence-interaction-*` use `children -> - label ...`
- `compare-binary-*` / `compare-hierarchy-left-right-*` have exactly two root nodes, with each side's content under its own `children`
- Each item under `children` explicitly contains `label`
- `chart-line-plain-text` uses one ordered `values` sequence
- Output contains no JSON, explanatory text or extra code blocks

## Generation workflow

### Step 1: understand the user's needs

Before creating the infographic, understand the user's needs and intended message so the template and data structure can be chosen.

If the user provides a clear content description, break it into a clear, concise structure.

Otherwise, clarify with the user (for example, “Please provide a clear, concise content description,” or “Which template would you like to use?”).

- Extract the main information structure (title, desc, items, etc.).
- Identify required data fields (title, desc, items, label, value, icon, etc.).
- Add `icon` proactively to main items with clear meaning; do not wait for a separate reminder.
- Choose a suitable template.
- Describe the infographic content `{syntax}` using AntV Infographic syntax.

**Key point**: respect the language of the user's input. For example, if the user writes in Chinese, text in the syntax must also be Chinese.

### Step 2: render the infographic

Once the AntV Infographic syntax is final, use these steps to generate a complete HTML file:

1. Create a complete HTML file with this structure:
   - DOCTYPE and HTML meta (charset: utf-8)
   - Title：`{title} - Infographic`
   - Load the AntV Infographic script: `./vendor/infographic-0.2.20.min.js`
   - Create a container div with id `container`
   - Initialize Infographic (`width: '100%'`, `height: '100%'`)
   - Replace `{title}` with the actual title
   - Replace `{syntax}` with the actual AntV Infographic syntax
   - Add SVG export: `const svgDataUrl = await infographic.toDataURL({ type: 'svg' });`

Reference HTML template:

```html
<div id="container"></div>
<script src="./vendor/infographic-0.2.20.min.js"></script>
<script>
 const infographic = new AntVInfographic.Infographic({
    container: '#container',
    width: '100%',
    height: '100%',
  });
  infographic.render(`{syntax}`);
  document.fonts?.ready.then(() => {
    infographic.render(`{syntax}`);
  }).catch((error) => console.error('Error waiting for fonts to load:', error));
</script>
```

2. Use the Write tool to generate an HTML file named `<title>-infographic.html`

3. Present it to the user:
   - Provide the generated file path and say, “Open it directly in a browser to view it and save SVG.”
   - Output the syntax and say, “Tell me if you would like to adjust the template, colors or content.”

**Note:** the HTML file must include:

- SVG export through an export button
- A responsive container with both width and height set to 100%


## Reproducible local renderer

The reviewed source package is @antv/infographic0.2.20 at commit5ae0d9394ac6280cb688eb4b4345881e291b9209. Commission its exact compatible immutable package/bundle and dependency integrity before rendering; retain the lock and MIT notice. Copy the verified local bundle to the referenced vendor path and use local rights-cleared icons/fonts/assets. No unpkg/latest or implicit remote font/icon fetch is a reproducible offline artifact. Retain the original DSL, editable HTML/SVG export and source data. Reopen the actual export and independently reconcile labels, values and units.
