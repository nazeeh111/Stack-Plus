"""Static scaffold compatibility checks, not an Obsidian rendering test.

The small evaluator covers only the documented filter expressions used by this
template. It fails on unfamiliar expressions rather than guessing app behavior.
"""
import pathlib
import re
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1] / 'templates/vault'


def scalar(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def properties(text):
    frontmatter = text.split('---', 2)[1]
    result = {}
    for line in frontmatter.strip().splitlines():
        key, value = line.split(':', 1)
        if key in result:
            raise AssertionError('Duplicate property: ' + key)
        result[key] = scalar(value)
    return result


def filter_expressions(block):
    """Read only a scalar filter or this scaffold's explicit AND list."""
    lines = block.splitlines()
    starts = [(index, re.fullmatch(r'( *)filters:\s*(.*)', line))
              for index, line in enumerate(lines) if re.fullmatch(r'( *)filters:\s*(.*)', line)]
    if len(starts) != 1:
        raise AssertionError('Expected exactly one explicit filter block')
    index, match = starts[0]
    if match[2]:
        return [scalar(match[2])]
    indent = len(match[1])
    body = []
    for line in lines[index + 1:]:
        if not line.strip():
            continue
        if len(line) - len(line.lstrip()) <= indent:
            break
        body.append(line)
    if not body or not re.fullmatch(r' +and:', body[0]):
        raise AssertionError('Unsupported static filter structure')
    and_indent = len(body[0]) - len(body[0].lstrip())
    expressions = []
    item_indent = None
    for line in body[1:]:
        item = re.fullmatch(r'( *)- (.+)', line)
        if not item or len(item[1]) not in (and_indent, and_indent + 2):
            raise AssertionError('Unsupported static filter structure: ' + line)
        if item_indent is None:
            item_indent = len(item[1])
        if len(item[1]) != item_indent:
            raise AssertionError('Unsupported nested static filter: ' + line)
        expressions.append(scalar(item[2]))
    if not expressions:
        raise AssertionError('Empty static filter list')
    return expressions


def selectors(base, view_name):
    """Read only the supported flat AND filters of the checked-in base."""
    global_block, views = base.split('views:\n', 1)
    expressions = filter_expressions(global_block)
    starts = list(re.finditer(r'(?m)^ *- type: [^\n]+\n', views))
    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(views)
        view = views[start.start():end]
        names = re.findall(r'^ +name: (.+)$', view, re.M)
        if names == [view_name]:
            return expressions + filter_expressions(view), view
    raise AssertionError('Missing view: ' + view_name)


def included(path, text, expressions):
    props = properties(text)
    matches = []
    for expression in expressions:
        if expression == 'file.ext == "md"':
            match = path.suffix == '.md'
        elif expression == 'file.hasTag("knowledge")':
            tags = props.get('tags', '').strip('[]').split(',')
            match = 'knowledge' in [tag.strip().strip('"\'') for tag in tags]
        elif re.fullmatch(r'!file.inFolder\("[^"\n]+"\)', expression):
            folder = expression.split('"')[1]
            match = folder not in path.parts[:-1]
        elif re.fullmatch(r'state == "[^"\n]+"', expression):
            match = props.get('state') == expression.split('"')[1]
        else:
            raise AssertionError('Unsupported static selector: ' + expression)
        matches.append(match)
    return all(matches)


class VaultTemplateTests(unittest.TestCase):
    def setUp(self):
        self.template = (ROOT / 'Templates/Knowledge Note.md').read_text()
        self.base = (ROOT / 'Knowledge Index.base').read_text()
        self.current, self.current_view = selectors(self.base, 'Current knowledge')
        self.historical, _ = selectors(self.base, 'Historical notes')

    def test_disposable_draft_becomes_current_with_visible_observation_date(self):
        with tempfile.TemporaryDirectory() as directory:
            note = pathlib.Path(directory) / 'Portable fixture.md'
            note.write_text(self.template)
            self.assertFalse(included(pathlib.Path('Library') / note.name,
                                      note.read_text(), self.current))
            checked = self.template.replace('state: draft', 'state: current')
            self.assertEqual(properties(checked)['observed_date'], '{{date:YYYY-MM-DD}}')
            checked = checked.replace('{{date:YYYY-MM-DD}}', '2026-11-10')
            note.write_text(checked)
            props = properties(note.read_text())
            self.assertTrue(included(pathlib.Path('Library') / note.name,
                                     note.read_text(), self.current))
            self.assertEqual(props['observed_date'], '2026-11-10')
            self.assertRegex(self.current_view, r'(?m)^ +- observed_date$')
            self.assertEqual(props['generation'], '1')
            self.assertEqual(props['supersedes'], 'none')
            self.assertNotIn('observation_date', props)
            self.assertNotIn('supersedes_generation', props)

    def test_current_view_excludes_archive_templates_untagged_and_other_formats(self):
        checked = self.template.replace('state: draft', 'state: current')
        for path in ['Archive/Fixture.md', 'Templates/Fixture.md', 'Library/Fixture.canvas']:
            with self.subTest(path=path):
                self.assertFalse(included(pathlib.Path(path), checked, self.current))
        self.assertFalse(included(pathlib.Path('Library/Fixture.md'),
                                  checked.replace('tags: [knowledge]', 'tags: []'), self.current))

    def test_unsupported_boolean_or_expression_fails_closed(self):
        unsupported = self.base.replace('    - state == "current"',
                                        '    - or:\n      - state == "current"', 1)
        with self.assertRaisesRegex(AssertionError, 'Unsupported nested static filter'):
            selectors(unsupported, 'Current knowledge')
        with self.assertRaisesRegex(AssertionError, 'Unsupported static selector'):
            included(pathlib.Path('Library/Fixture.md'), self.template, ['state != "draft"'])

    def test_historical_reports_are_separate_from_current_claims(self):
        historical = self.template.replace('state: draft', 'state: historical-source-report')
        path = pathlib.Path('Library/Historical fixture.md')
        self.assertFalse(included(path, historical, self.current))
        self.assertTrue(included(path, historical, self.historical))
        # Retain the former indented-view/scalar-filter form as an explicit
        # supported fixture, without treating this helper as a YAML parser.
        legacy = '''filters:
  and:
    - file.ext == "md"
    - file.hasTag("knowledge")
    - '!file.inFolder("Templates")'
    - '!file.inFolder("Archive")'
views:
  - type: table
    name: Historical notes
    filters: state == "historical-source-report"
'''
        expressions, _ = selectors(legacy, 'Historical notes')
        self.assertTrue(included(path, historical, expressions))
        self.assertFalse(included(path, self.template, expressions))
        with self.assertRaisesRegex(AssertionError, 'Unsupported static selector'):
            included(path, historical, ['state == "draft"', 'file.unknownOperation()'])
        with self.assertRaisesRegex(AssertionError, 'Unsupported static filter structure'):
            selectors(legacy.replace('  and:', '  not:'), 'Historical notes')


if __name__ == '__main__':
    unittest.main()
