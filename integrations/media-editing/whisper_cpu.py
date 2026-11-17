"""Bounded local Whisper CLI invocation with fresh artifact admission.

No installation, model discovery, downloads, account/config reads or provider calls.
Caller supplies an already admitted CLI/model and their expected SHA256 hashes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import pathlib
import re
import stat
import subprocess
import time
import wave


class AdmissionError(RuntimeError):
    pass


def regular_file(path):
    path = pathlib.Path(path)
    if not stat.S_ISREG(path.stat().st_mode):
        raise AdmissionError('An explicit regular file is required: ' + path.name)
    return path


def sha(path):
    # Inputs must remain stable for the run. This is not concurrent-writer isolation.
    path = regular_file(path)
    digest = hashlib.sha256()
    with path.open('rb') as data:
        for chunk in iter(lambda: data.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def stamp_ms(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{2,}:\d{2}:\d{2}[,.]\d{3}', value):
        raise AdmissionError('Invalid caption timestamp')
    h, m, s, fraction = map(int, re.split('[:,.]', value))
    if m >= 60 or s >= 60:
        raise AdmissionError('Invalid caption clock fields')
    return ((h * 60 + m) * 60 + s) * 1000 + fraction


def clean(text):
    return ' '.join(text.split())


def admit_outputs(folder, duration_ms, expect_speech=False):
    folder = pathlib.Path(folder)
    paths = {ext: folder / ('transcript.' + ext) for ext in ('json', 'srt', 'txt')}
    for p in paths.values():
        if p.is_symlink() or not p.is_file():
            raise AdmissionError('Missing or symlinked required output: ' + p.name)
    try:
        data = json.loads(paths['json'].read_text(encoding='utf-8'))
    except (ValueError, UnicodeError) as exc:
        raise AdmissionError('Invalid transcript JSON') from exc
    if not isinstance(data, dict) or not isinstance(data.get('transcription'), list):
        raise AdmissionError('JSON has no transcription array')
    expected = []
    previous = 0
    for seg in data['transcription']:
        if not isinstance(seg, dict) or not isinstance(seg.get('text'), str):
            raise AdmissionError('Invalid transcript segment')
        offsets, times = seg.get('offsets'), seg.get('timestamps')
        if not isinstance(offsets, dict) or not isinstance(times, dict):
            raise AdmissionError('Segment has no offsets/timestamps')
        a, b = offsets.get('from'), offsets.get('to')
        if type(a) is not int or type(b) is not int:
            raise AdmissionError('Offsets must be integer milliseconds')
        if not 0 <= a <= b <= duration_ms or a < previous:
            raise AdmissionError('Segment timing is unordered or outside source')
        if stamp_ms(times.get('from')) != a or stamp_ms(times.get('to')) != b:
            raise AdmissionError('Offset units disagree with formatted timestamps')
        previous = b
        text = clean(seg['text'])
        if text:
            if b == a:
                raise AdmissionError('Nonempty segment has zero duration')
        # Keep blank segments too: upstream emits a matching initial blank SRT cue.
        # Omitting them here would admit extra or backwards empty cues in SRT.
        expected.append((a, b, text))
    try:
        srt = paths['srt'].read_text(encoding='utf-8').strip()
        text_file = clean(paths['txt'].read_text(encoding='utf-8'))
    except UnicodeError as exc:
        raise AdmissionError('Caption outputs are not UTF-8') from exc
    actual = []
    previous = 0
    if srt:
        for number, block in enumerate(re.split(r'\n\s*\n', srt), 1):
            lines = block.splitlines()
            if len(lines) < 2 or lines[0].strip() != str(number):
                raise AdmissionError('Invalid SRT cue numbering')
            pair = lines[1].split(' --> ')
            if len(pair) != 2:
                raise AdmissionError('Invalid SRT cue interval')
            a, b = map(stamp_ms, pair)
            if not 0 <= a <= b <= duration_ms or a < previous:
                raise AdmissionError('SRT interval unordered or outside source')
            previous = b
            text = clean(' '.join(lines[2:]))
            actual.append((a, b, text))
    if actual != expected or text_file != clean(' '.join(x[2] for x in expected)):
        raise AdmissionError('JSON, SRT and TXT do not describe the same transcript')
    nonempty = sum(bool(x[2]) for x in expected)
    if expect_speech and not nonempty:
        raise AdmissionError('Expected speech but producer returned an empty transcript')
    return {'status': 'transcribed' if nonempty else 'empty_transcript',
            'segments': nonempty, 'duration_ms': duration_ms,
            'artifacts': {p.name: sha(p) for p in paths.values()}}


def transcribe(cli, model, source, output, *, cli_sha256, model_sha256,
               threads=4, timeout=300, max_seconds=1800, expect_speech=False):
    if not 1 <= threads <= 16 or not math.isfinite(timeout) or timeout <= 0:
        raise AdmissionError('Use 1–16 CPU threads and a positive finite timeout')
    if not math.isfinite(max_seconds) or max_seconds <= 0:
        raise AdmissionError('Use a positive finite source-duration bound')
    cli, model, source = (pathlib.Path(p).resolve(strict=True) for p in (cli, model, source))
    for path in (cli, model, source):
        regular_file(path)
    for label, path, digest in [('CLI', cli, cli_sha256), ('model', model, model_sha256)]:
        if not re.fullmatch('[0-9a-f]{64}', digest) or sha(path) != digest:
            raise AdmissionError(label + ' hash differs from the admitted artifact')
    try:
        with wave.open(str(source), 'rb') as audio:
            if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate(), audio.getcomptype()) != (1, 2, 16000, 'NONE'):
                raise AdmissionError('This route accepts mono 16-bit PCM WAV at 16kHz')
            frames = audio.getnframes()
            if frames <= 0 or frames / 16000 > max_seconds:
                raise AdmissionError('Empty audio or source exceeds the duration bound')
            # getnframes() trusts the data-chunk declaration. Read the bounded PCM
            # payload to establish actual duration before any producer is launched.
            remaining = frames
            while remaining:
                pcm = audio.readframes(min(remaining, 65536))
                if not pcm or len(pcm) % 2:
                    raise AdmissionError('Truncated WAV or partial PCM frame')
                remaining -= len(pcm) // 2
            if audio.readframes(1):
                raise AdmissionError('WAV data contains a partial or extra PCM frame')
            duration_ms = frames * 1000 / 16000
    except (wave.Error, EOFError) as exc:
        raise AdmissionError('Input is not an admitted PCM WAV file') from exc
    output = pathlib.Path(output).absolute()
    # Existing runs are never overwritten or reused, including failed/partial runs.
    output.mkdir(parents=False, exist_ok=False)
    argv = [str(cli), '--no-gpu', '--threads', str(threads), '--language', 'en',
            '--no-fallback', '--beam-size', '1', '--best-of', '1', '--temperature', '0',
            '--model', str(model), '--file', str(source), '--output-json-full',
            '--output-srt', '--output-txt', '--max-len', '1', '--split-on-word',
            '--output-file', str(output / 'transcript')]
    record = {'status': 'running', 'input': {'path': str(source), 'sha256': sha(source)},
              'cli_sha256': cli_sha256, 'model_sha256': model_sha256, 'argv': argv,
              'cpu_threads': threads, 'timeout_seconds': timeout,
              'max_source_seconds': max_seconds, 'expect_speech': expect_speech}
    receipt = output / 'RUN.json'
    receipt.write_text(json.dumps(record, indent=2) + '\n')
    start = time.monotonic()
    try:
        with (output / 'producer.stdout').open('wb') as stdout, (output / 'producer.stderr').open('wb') as stderr:
            producer = subprocess.run(argv, cwd=output, stdout=stdout, stderr=stderr,
                                      env={'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL': 'C'},
                                      timeout=timeout)
        record['producer_exit'] = producer.returncode
        if producer.returncode != 0:
            raise AdmissionError('Producer failed with exit ' + str(producer.returncode))
        record.update(admit_outputs(output, duration_ms, expect_speech))
        if sha(cli) != cli_sha256 or sha(model) != model_sha256 or sha(source) != record['input']['sha256']:
            raise AdmissionError('An admitted input changed during transcription')
    except (Exception, KeyboardInterrupt) as exc:
        record.update(status='failed', error=type(exc).__name__ + ': ' + str(exc))
        raise
    finally:
        record['elapsed_seconds'] = time.monotonic() - start
        receipt.write_text(json.dumps(record, indent=2) + '\n')
    return record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('cli', 'model', 'source', 'output', 'cli-sha256', 'model-sha256'):
        p.add_argument('--' + name, required=True)
    p.add_argument('--threads', type=int, default=4)
    p.add_argument('--timeout', type=float, default=300)
    p.add_argument('--max-seconds', type=float, default=1800)
    p.add_argument('--expect-speech', action='store_true')
    a = p.parse_args()
    result = transcribe(a.cli, a.model, a.source, a.output, cli_sha256=a.cli_sha256,
                        model_sha256=a.model_sha256, threads=a.threads, timeout=a.timeout,
                        max_seconds=a.max_seconds, expect_speech=a.expect_speech)
    print(json.dumps({'status': result['status'], 'segments': result['segments'],
                      'receipt': str(pathlib.Path(a.output).absolute() / 'RUN.json')}))


if __name__ == '__main__':
    main()
