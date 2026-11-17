import importlib.util
import json
import os
import pathlib
import struct
import subprocess
import sys
import tempfile
import unittest
import wave

MODULE = pathlib.Path(__file__).resolve().parents[1] / 'integrations/media-editing/whisper_cpu.py'
spec = importlib.util.spec_from_file_location('whisper_cpu', MODULE)
asr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asr)


class WhisperAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='nstack-asr-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.model = self.root / 'model.bin'
        self.model.write_bytes(b'synthetic model, never loaded')
        self.source = self.root / 'source.wav'
        with wave.open(str(self.source), 'wb') as w:
            w.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
            w.writeframes(bytes(32000))

    def producer(self, mode='valid'):
        script = self.root / ('producer-' + mode)
        script.write_text('#!' + sys.executable + '\n' + '''
import json,pathlib,sys,time
mode=MODE
prefix=pathlib.Path(sys.argv[sys.argv.index('--output-file')+1])
assert '--no-gpu' in sys.argv
if mode=='timeout':
    (prefix.parent/'partial.txt').write_text('retained')
    time.sleep(2)
if mode=='nothing':sys.exit(0)
segments=[] if mode=='empty' else [{'text':' Hello', 'offsets':{'from':100,'to':900}, 'timestamps':{'from':'00:00:00,100','to':'00:00:00,900'}}]
if mode=='outside':segments[0]['offsets']['to']=1100;segments[0]['timestamps']['to']='00:00:01,100'
if mode=='units':segments[0]['offsets']['from']=10
if mode=='blankmatch':segments.insert(0,{'text':' ', 'offsets':{'from':0,'to':100}, 'timestamps':{'from':'00:00:00,000','to':'00:00:00,100'}})
prefix.with_suffix('.json').write_text(json.dumps({'transcription':segments}))
prefix.with_suffix('.srt').write_text('' if mode=='empty' else '1\\n00:00:00,100 --> 00:00:00,900\\nHello\\n')
prefix.with_suffix('.txt').write_text('' if mode=='empty' else 'Hello\\n')
if mode=='blankmatch':prefix.with_suffix('.srt').write_text('1\\n00:00:00,000 --> 00:00:00,100\\n \\n\\n2\\n00:00:00,100 --> 00:00:00,900\\nHello\\n')
if mode in ('extrablank','backwardblank'):
    cue='00:00:00,900 --> 00:00:01,000' if mode=='extrablank' else '00:00:00,000 --> 00:00:00,050'
    with prefix.with_suffix('.srt').open('a') as f:f.write('\\n2\\n'+cue+'\\n \\n')
if mode=='brokenjson':prefix.with_suffix('.json').write_text('{partial')
if mode=='shape':prefix.with_suffix('.json').write_text('[]')
if mode=='mismatch':prefix.with_suffix('.txt').write_text('Different text')
if mode=='symlink':
    p=prefix.with_suffix('.json');target=prefix.parent/'old.json';p.rename(target);p.symlink_to(target)
if mode=='failed':sys.exit(7)
'''.replace('MODE', repr(mode)))
        script.chmod(0o700)
        return script

    def invoke(self, mode='valid', **kwargs):
        cli = self.producer(mode)
        return asr.transcribe(cli, self.model, self.source, self.root / 'run',
                              cli_sha256=asr.sha(cli), model_sha256=asr.sha(self.model),
                              **kwargs)

    def test_matching_new_artifacts_are_admitted(self):
        r = self.invoke(expect_speech=True)
        self.assertEqual(r['status'], 'transcribed')
        self.assertEqual(r['segments'], 1)
        self.assertEqual(r['producer_exit'], 0)

    def test_exit_zero_without_output_is_failure_with_evidence(self):
        with self.assertRaises(asr.AdmissionError):
            self.invoke('nothing')
        r = json.loads((self.root / 'run/RUN.json').read_text())
        self.assertEqual((r['status'], r['producer_exit']), ('failed', 0))
        self.assertTrue((self.root / 'run/producer.stderr').is_file())

    def test_nonzero_producer_is_rejected_even_with_valid_output(self):
        with self.assertRaises(asr.AdmissionError):
            self.invoke('failed')
        self.assertTrue((self.root / 'run/transcript.json').is_file())
        self.assertEqual(json.loads((self.root / 'run/RUN.json').read_text())['producer_exit'], 7)

    def test_empty_result_is_explicit(self):
        self.assertEqual(self.invoke('empty')['status'], 'empty_transcript')

    def test_expected_speech_refuses_empty_result(self):
        with self.assertRaises(asr.AdmissionError):
            self.invoke('empty', expect_speech=True)

    def test_timings_cannot_exceed_actual_audio(self):
        with self.assertRaises(asr.AdmissionError):
            self.invoke('outside')

    def test_offset_unit_mismatch_is_rejected(self):
        with self.assertRaises(asr.AdmissionError):
            self.invoke('units')

    def test_three_formats_must_describe_same_transcript(self):
        with self.assertRaises(asr.AdmissionError):
            self.invoke('mismatch')

    def test_partial_json_is_rejected(self):
        with self.assertRaises(asr.AdmissionError):
            self.invoke('brokenjson')

    def test_json_without_transcription_shape_is_rejected(self):
        with self.assertRaises(asr.AdmissionError):
            self.invoke('shape')

    def test_output_symlink_is_not_accepted_as_new_artifact(self):
        with self.assertRaises(asr.AdmissionError):
            self.invoke('symlink')

    def test_existing_run_is_preserved_without_execution(self):
        self.invoke()
        receipt = (self.root / 'run/RUN.json').read_bytes()
        with self.assertRaises(FileExistsError):
            self.invoke('nothing')
        self.assertEqual((self.root / 'run/RUN.json').read_bytes(), receipt)

    def test_hash_mismatch_prevents_execution(self):
        cli = self.producer()
        with self.assertRaises(asr.AdmissionError):
            asr.transcribe(cli, self.model, self.source, self.root / 'run',
                           cli_sha256='0' * 64, model_sha256=asr.sha(self.model))
        self.assertFalse((self.root / 'run').exists())

    def test_duration_bound_prevents_execution(self):
        with self.assertRaises(asr.AdmissionError):
            self.invoke(max_seconds=.5)
        self.assertFalse((self.root / 'run').exists())

    def test_truncated_declared_pcm_prevents_execution(self):
        self.source.write_bytes(self.source.read_bytes()[:76])
        with self.assertRaises(asr.AdmissionError):
            self.invoke(expect_speech=True)
        self.assertFalse((self.root / 'run').exists())

    def test_partial_pcm_frame_prevents_execution(self):
        data = bytearray(self.source.read_bytes())
        data.append(0)
        struct.pack_into('<I', data, 4, len(data) - 8)
        struct.pack_into('<I', data, 40, 32001)
        self.source.write_bytes(data)
        with self.assertRaises(asr.AdmissionError):
            self.invoke()
        self.assertFalse((self.root / 'run').exists())

    def test_nonregular_paths_are_rejected_without_fifo_read(self):
        cli = self.producer()
        fifo = self.root / 'named-pipe'
        os.mkfifo(fifo)
        cli_hash, model_hash = asr.sha(cli), asr.sha(self.model)
        for role in ('cli', 'model', 'source'):
            with self.subTest(role=role):
                args = {'cli': cli, 'model': self.model, 'source': self.source}
                args[role] = fifo
                # Outer deadline makes a reintroduced blocking read fail this test
                # instead of hanging the test runner. No producer is permitted.
                code = f'''import importlib.util
s=importlib.util.spec_from_file_location('asr',{str(MODULE)!r})
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.transcribe({str(args['cli'])!r},{str(args['model'])!r},{str(args['source'])!r},{str(self.root / ('fifo-' + role))!r},cli_sha256={cli_hash!r},model_sha256={model_hash!r},timeout=.05)
'''
                result = subprocess.run([sys.executable, '-B', '-c', code],
                                        capture_output=True, text=True, timeout=1)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('regular file is required', result.stderr)
                self.assertFalse((self.root / ('fifo-' + role)).exists())

    def test_matching_blank_cue_is_preserved_in_complete_format_comparison(self):
        r = self.invoke('blankmatch', expect_speech=True)
        self.assertEqual((r['status'], r['segments']), ('transcribed', 1))

    def test_extra_forward_empty_srt_cue_is_rejected(self):
        with self.assertRaises(asr.AdmissionError):
            self.invoke('extrablank')

    def test_extra_backward_empty_srt_cue_is_rejected(self):
        with self.assertRaises(asr.AdmissionError):
            self.invoke('backwardblank')

    def test_timeout_retains_partial_output_and_failed_receipt(self):
        with self.assertRaises(__import__('subprocess').TimeoutExpired):
            self.invoke('timeout', timeout=.15)
        self.assertEqual((self.root / 'run/partial.txt').read_text(), 'retained')
        self.assertEqual(json.loads((self.root / 'run/RUN.json').read_text())['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
