"""Canonical exposure names; source coordinates and workflow routing stay separate."""
import hashlib
import json
from pathlib import Path
import re

RENAMES = {
    "frontend-design": "web-ui-design",
    "unslop": "ui-polish",
    "impeccable-audit": "ui-quality-audit",
    "impeccable-harden": "ui-reliability",
    "taste-skill": "ui-art-direction",
    "core": "browser-cli-guide",
    "codex-skill": "cli-anything-harnesses",
    "composition-patterns": "react-composition-patterns",
    "fp-check": "security-finding-verification",
    "differential-review": "security-change-review",
    "media-use": "hyperframes-media",
    "product-marketing": "product-marketing-context",
    "launch": "product-launch-strategy",
    "emails": "email-sequences",
    "interview-script": "customer-interview-script",
    "synthesize-research": "user-research-synthesis",
    "cloudflare-security-audit": "code-security-review",
    "finance-audit-xls": "spreadsheet-formula-audit",
    "tdd": "test-driven-development",
    "codebase-design": "module-interface-design",
    "gstack-office-hours": "gstack-product-consultation",
    "react-best-practices": "react-nextjs-performance",
    "migration-architect": "migration-planning",
    "pstack-architect": "code-architecture-planning",
    "pstack-blast-radius": "change-impact-review",
    "pstack-shared-state": "concurrent-state-ownership",
    "pstack-idempotency": "idempotent-operation-design",
    "pstack-benchmark": "performance-benchmark-review",
    "supabase-postgres-best-practices": "postgres-performance-and-design",
    "scrapling-skill": "scrapling-web-extraction",
    "memory-leak-debugging": "javascript-memory-leaks",
    "cua-driver": "cua-driver-gui-fallback",
    "gws-shared": "google-workspace-cli",
    "n8n-validation-expert": "n8n-workflow-validation",
    "n8n-mcp-tools-expert": "n8n-mcp-tool-guide",
    "peer-review": "scientific-peer-review",
    "qiskit": "qiskit-quantum-circuits",
    "qutip": "qutip-quantum-dynamics",
    "pennylane": "pennylane-differentiable-circuits",
    "result-to-claim": "experiment-claim-validation",
    "hf-cli": "huggingface-hub-cli",
    "hf-mem": "huggingface-model-memory",
    "huggingface-datasets": "huggingface-dataset-viewer-api",
    "huggingface-gradio": "gradio-python-web-apps",
    "huggingface-spaces": "huggingface-spaces-hosting",
    "cocoindex": "cocoindex-incremental-indexing",
    "dimensional-analysis": "code-unit-scaling-audit",
    "semgrep": "semgrep-security-scan",
    "codeql": "codeql-security-analysis",
    "hyperframes": "hyperframes-video-production",
    "hyperframes-cli": "hyperframes-video-cli",
    "hyperframes-registry": "hyperframes-video-components",
    "remotion-best-practices": "remotion-video-workflows",
    "remotion-create": "remotion-video-creation",
    "remotion-markup": "remotion-animation-markup",
    "remotion-render": "remotion-video-export",
    "auto-editor": "auto-editor-audio-video-cuts",
    "auto-editor-export": "auto-editor-timeline-conversion",
    "godot-production-checks": "godot-project-validation",
    "kicad": "kicad-pcb-schematic-analysis",
    "datasheets": "component-datasheet-extraction",
    "spice": "spice-circuit-simulation",
    "emc": "pcb-emc-risk-review",
    "copywriting": "marketing-copywriting",
    "pricing": "product-pricing-strategy",
    "identify-assumptions-new": "new-product-assumption-review",
    "seo-technical": "technical-seo-audit",
    "seo-audit": "sitewide-seo-audit",
    "ads-math": "paid-media-financial-modeling",
    "career-ops": "career-ops-job-search",
    "gh-fix-ci": "github-actions-ci-repair",
    "gh-address-comments": "github-pr-comment-resolution",
    "gcloud": "google-cloud-cli",
    "eve": "eve-durable-agent-apps",
    "scenario-blender-expert": "blender-production-workflows",
    "scenario-blender-hard-surface": "blender-hard-surface-modeling",
    "scenario-blender-rigging": "blender-rigging",
    "scenario-blender-previs-storyboard": "blender-previs-storyboarding",
    "scenario-blender-animation": "blender-animation",
    "scenario-blender-texturing-shading": "blender-texturing-shading",
    "scenario-blender-lighting-rendering": "blender-lighting-rendering",
    "scenario-blender-export": "blender-asset-export",
    "scenario-unreal-expert": "unreal-project-development",
    "scenario-unreal-cinematics": "unreal-cinematic-production",
    "colorfigures": "colorfigures-interactive-explainers",
    "archify": "archify-diagrams-and-explainers",
    "prospecting": "sales-account-prospecting",
    "cold-email": "cold-email-drafts",
    "last30days": "recent-practitioner-research",
    "trufflehog-scan": "trufflehog-secret-scan",
    "motion-canvas-production": "motion-canvas-vector-animation",
    "baoyu-comic": "educational-comics",
    "slidev-production": "slidev-presentations",
    "finance-3-statement-model": "finance-3-statement-completion",
    "finance-comps-analysis": "finance-comparable-company-valuation",
    "training-tuning-playbook": "deep-learning-training-diagnostics",
    "worktrunk": "worktrunk-git-worktrees",
    "euclidean-geometry-ddar": "euclidean-geometry-ddar-solving",
    "instrument-control": "lab-instrument-control",
    "pstack-statechart": "tla-state-machine-checking",
    "gstack-qa": "gstack-test-fix-verify",
    "gstack-review": "gstack-diff-review",
    "gstack-plan-eng-review": "gstack-engineering-plan-review",
    "remotion-interactivity": "remotion-editable-video-markup",
    "remotion-studio": "remotion-video-preview",
    "remotion-multimedia": "remotion-media-processing",
    "manim-production": "manim-math-animation",
    "scenario-unreal-animation": "unreal-animation",
    "scenario-unreal-pipeline-automation": "unreal-pipeline-automation",
    "scenario-blender-grease-pencil": "blender-2d-drawing-animation",
    "academic-paper": "academic-manuscript-writing",
    "academic-paper-reviewer": "academic-paper-panel-review",
    "academic-pipeline": "academic-research-to-manuscript",
    "agent-orchestration": "multi-model-agent-orchestration",
    "agent-reach": "agent-reach-platform-reading",
    "council-of-high-intelligence": "persona-decision-council",
    "craft-anything": "craft-anything-software-investigation",
    "deep-research": "academic-deep-research",
    "eval-harness": "agent-evaluation-harness",
    "llm-council": "llm-council-answer-review",
    "playwright-mcp": "playwright-mcp-browser-automation",
    "raea": "raea-gpu-video-and-games",
    "rea": "rea-software-analysis",
    "roast-room": "business-council-roast-room",
    "skillspector": "skill-source-audit",
    "sr-screener": "study-eligibility-screening"
}

# Reviewed host invocations only: source leaf -> exact operative path -> literal
# token/phrase -> referenced source skill. CLI catalogs, code paths and archives
# are intentionally absent. Some host usage examples live in plain code fences.
HOST_INVOCATIONS = {
    'hyperframes': {path: {'`/media-use`': 'media-use'} for path in (
        'skills/hyperframes/SKILL.md',
        'skills/hyperframes/references/captions.md',
        'skills/hyperframes/references/sound.md',
        'skills/hyperframes/references/format.md',
        'skills/hyperframes/references/types/launch.md',
    )},
    'hyperframes-cli': {
        **{path: {'`/media-use`': 'media-use'} for path in (
            'skills/hyperframes-cli/SKILL.md',
            'skills/hyperframes-cli/references/compare-and-batch.md',
            'skills/hyperframes/references/format.md',
        )},
        'skills/hyperframes-cli/references/init-and-scaffold.md': {
            'see the `media-use` skill': 'media-use',
        },
        'skills/hyperframes-cli/references/upgrade-info-misc.md': {
            'invoke the `media-use` skill': 'media-use',
        },
    },
    'product-marketing': {'SKILL.md': {'`/product-marketing`': 'product-marketing'}},
    'synthesize-research': {'product-management/skills/synthesize-research/SKILL.md': {
        '\n/synthesize-research $ARGUMENTS': 'synthesize-research',
    }},
    'unslop': {'README.md': {
        '`/unslop`': 'unslop', '`$unslop`': 'unslop', '\n/unslop ': 'unslop',
    }},
}
PORT_RECEIPT = 'EXPOSURE-PORT.json'
ORIGINALS = 'EXPOSURE-ORIGINALS'
HOST_NOTES = {'unslop': {'README.md': (
    '> nstack profile: the host invocation examples below use `{exposed}`. '
    'The unchanged upstream source/install paths install the upstream name, '
    'rather than this nstack exposure.\n\n'
)}}
DESCRIPTIONS = {
    'pstack-architect': {
        'source': "Sketch types, signatures, and module structure before code, then stay in the loop while implementation fills in. Use for /architect, 'architect this', 'design this', or non-trivial work where jumping to code would lock in the wrong shape.",
        'exposed': 'Design and synthesize competing code-architecture sketches through pstack arena, then implement the selected design. Use for substantial architecture decisions that benefit from independent alternatives.',
    },
    'gstack-office-hours': {
        'source': 'YC Office Hours — two modes. (gstack)',
        'exposed': 'Diagnose a startup or product idea, or explore a builder project as a design partner, using gstack Office Hours. Use for problem framing, alternatives and a practical design before implementation.',
    },
    'gstack-plan-eng-review': {
        'source': 'Eng manager-mode plan review. (gstack)',
        'exposed': 'Review an engineering plan for architecture, scope, failure modes, test coverage and rollout using gstack engineering review.',
    },
}
_UNREAL_SOURCE_DESCRIPTION = ('Version-checked native Unreal project or cinematic work using the actual installed engine and selected local technique helpers. '
                              'Preserve C++/Blueprint gameplay; no global Scenario service or fixed Mac engine path is assumed.')
DESCRIPTIONS.update({source: {'source': _UNREAL_SOURCE_DESCRIPTION, 'exposed': text} for source, text in {
    'scenario-unreal-expert': 'Choose a version-checked Unreal execution channel and run a measured build, audit, profile and visual-review workflow. Use for technical direction, capability checks and cross-domain project work with the actual installed engine and local helpers.',
    'scenario-unreal-animation': 'Develop Unreal animation workflows for skeleton import, IK retargeting, capsule-matched locomotion, motion matching, root motion and foot contact. Use version-checked native APIs and local helpers; offline checks do not establish editor validation.',
    'scenario-unreal-cinematics': 'Produce Unreal cinematics with Sequencer shots and Movie Render Graph: cut timing, cameras, pre-roll, lighting, render manifests and EXR delivery. Use the actual installed engine and selected local technique helpers.',
    'scenario-unreal-pipeline-automation': 'Automate Unreal asset import and reimport, validation, LOD and collision processing, batch jobs, cooking, packaging and boot checks. Use explicit job policies and version-checked native APIs and local helpers.',
}.items()})
# Only offsets, small source-ID tokens and hashes; no private source prose.
HOST_LINES = json.loads(Path(__file__).with_name('skill_host_bindings.json').read_text())


def canonical(name):
    return RENAMES.get(name, name)


def source_name(name):
    return next((source for source, exposed in RENAMES.items() if exposed == name), name)


def metadata(name):
    source = source_name(name)
    return {'source_name': source, 'aliases': [source] if source != name else []}


def policy():
    """Seal the full naming policy so changed exposure rules invalidate releases."""
    return {'version': 3, 'renames': dict(RENAMES), 'host_invocations': HOST_INVOCATIONS,
            'host_notes': HOST_NOTES, 'descriptions': DESCRIPTIONS, 'host_lines': HOST_LINES}


def description(raw):
    header = raw.decode().split('---', 2)[1]
    matches = re.findall(r'(?m)^description:\s*(.*)$', header)
    if len(matches) != 1:
        raise ValueError('Exposure description requires one inline metadata field')
    value = matches[0].strip()
    return json.loads(value) if value.startswith('"') else value


def entry_name(raw, name):
    text, count = re.subn(r'(?m)^name:.*$', 'name: ' + name, raw.decode(), count=1)
    if count != 1:
        raise ValueError('Selected entry lacks a unique name')
    source = source_name(name)
    if source in DESCRIPTIONS:
        override = DESCRIPTIONS[source]
        if description(raw) not in (override['source'], override['exposed']):
            raise ValueError('Reviewed exposure description changed: ' + name)
        text = re.sub(r'(?m)^description:.*$', 'description: ' + json.dumps(override['exposed']), text, count=1)
    return text.encode()


def host_lines(source, relative, raw):
    """Patch only reviewed occurrences in exact preimage lines before metadata."""
    plan = HOST_LINES.get(source, {}).get(relative, {})
    active = {number: record for number, record in plan.items()
              if any(canonical(edit['source']) != edit['source'] for edit in record['edits'])}
    if not active:
        return raw, {}
    lines, applied = raw.decode().splitlines(keepends=True), {}
    for number, record in active.items():
        index = int(number) - 1
        if not 0 <= index < len(lines):
            raise ValueError('Reviewed host binding line missing: ' + source + '/' + relative + ':' + number)
        parts = lines[index].splitlines()
        content = parts[0] if parts else ''
        ending = lines[index][len(content):]
        if hashlib.sha256(content.encode()).hexdigest() != record['sha256']:
            raise ValueError('Reviewed host binding preimage changed: ' + source + '/' + relative + ':' + number)
        edits = []
        for edit in sorted(record['edits'], key=lambda item: item['offset'], reverse=True):
            offset, literal = edit['offset'], edit['literal']
            if offset < 0 or content[offset:offset + len(literal)] != literal:
                raise ValueError('Reviewed host binding offset changed: ' + source + '/' + relative + ':' + number)
            rendered = literal.replace(edit['source'], canonical(edit['source']))
            if rendered != literal:
                content = content[:offset] + rendered + content[offset + len(literal):]
                edits.append({**edit, 'rendered': rendered})
        lines[index] = content + ending
        if edits:
            applied[number] = {'preimage_sha256': record['sha256'], 'edits': edits}
    return ''.join(lines).encode(), applied


def expose_files(source, files, entry=None, name=None):
    """Pure closed-map adaptation, retaining changed originals and an exact receipt."""
    required = {path for path, bindings in HOST_INVOCATIONS.get(source, {}).items()
                if any(canonical(reference) != reference for reference in bindings.values())}
    required.update(path for path, lines in HOST_LINES.get(source, {}).items()
                    if any(canonical(edit['source']) != edit['source']
                           for line in lines.values() for edit in line['edits']))
    if required - files.keys():
        raise ValueError('Reviewed host binding file missing: ' + source + '/' + sorted(required - files.keys())[0])
    result, changes = dict(files), {}
    for relative, (raw, mode) in files.items():
        metadata_changed = (relative == entry and source in DESCRIPTIONS
                            and description(raw) != DESCRIPTIONS[source]['exposed'])
        bound, line_changes = host_lines(source, relative, raw)
        data = entry_name(bound, name) if name is not None and relative == entry else bound
        rendered = data
        replacements = {}
        for literal, referenced in HOST_INVOCATIONS.get(source, {}).get(relative, {}).items():
            exposed = canonical(referenced)
            if exposed == referenced:
                continue
            before, after = literal.encode(), literal.replace(referenced, exposed).encode()
            count = rendered.count(before)
            if not count:
                raise ValueError('Reviewed host invocation anchor missing: ' + source + '/' + relative)
            rendered = rendered.replace(before, after)
            replacements[literal] = {'rendered': after.decode(), 'occurrences': count}
        if replacements and relative in HOST_NOTES.get(source, {}):
            rendered = HOST_NOTES[source][relative].format(exposed=canonical(source)).encode() + rendered
        result[relative] = (rendered, mode)
        if rendered != data or metadata_changed or line_changes:
            original = ORIGINALS + '/' + relative + '.original'
            if original in files or PORT_RECEIPT in files:
                raise ValueError('Exposure provenance collision: ' + source + '/' + relative)
            result[original] = (raw, mode)
            changes[relative] = {'before_sha256': hashlib.sha256(raw).hexdigest(),
                                 'after_sha256': hashlib.sha256(rendered).hexdigest(),
                                 'original': original, 'replacements': replacements}
            if metadata_changed:
                changes[relative]['description'] = DESCRIPTIONS[source]['exposed']
            if line_changes:
                changes[relative]['host_lines'] = line_changes
    if changes:
        receipt = {'policy_version': policy()['version'], 'source_name': source,
                   'scope': 'Reviewed host invocations, exposure bindings and entry metadata; pre-exposure bytes retained.',
                   'files': changes}
        result[PORT_RECEIPT] = ((json.dumps(receipt, sort_keys=True, indent=2) + '\n').encode(), 0o444)
    return result
