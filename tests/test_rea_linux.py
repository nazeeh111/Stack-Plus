import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location('rea_linux', Path(__file__).resolve().parents[1] / 'recipes/rea_linux.py')
rea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rea)

class BoundaryTests(unittest.TestCase):
    def test_runtime_execution_tools_are_refused_even_by_direct_name(self):
        for name in ['gdb_console','execute_rizin_command','capture_process_scenario','capture_browser_scenario','start_frida_session','observe_native_calls','install_adb_package','start_build_computer','unknown']:
            with self.subTest(name=name), self.assertRaises(ValueError): rea.validate_call(name,{})
        self.assertEqual(rea.validate_call('open_binary',{'path':'/input/a'})['provider_id'],'ghidra')
        with self.assertRaises(ValueError): rea.validate_call('open_binary',{'path':'/input/a','provider_id':'hopper'})

    def test_host_and_guest_traversal_cannot_escape_declared_input(self):
        source=Path('/private/tmp/authorized'); task=Path('/private/tmp/task')
        self.assertEqual(rea.map_paths({'input_path':str(source/'main.js')},source,task),{'input_path':'/input/main.js'})
        for path in [str(source/'../../etc/passwd'),'/input/../../etc/passwd','/etc/passwd','/Users/somebody/.ssh/id']:
            with self.subTest(path=path),self.assertRaises(ValueError):rea.map_paths({'input_path':path},source,task)

    def test_nested_sensitive_or_linked_sources_are_never_copied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve(); source=root/'source';source.mkdir();(source/'normal').write_text('ok');(source/'credentials').mkdir()
            with self.assertRaises(ValueError):rea.snapshot(source,root/'copy')
            self.assertFalse((root/'copy').exists())
            (source/'credentials').rmdir();(source/'link').symlink_to('/etc/passwd')
            with self.assertRaises(ValueError):rea.snapshot(source,root/'copy')

    def test_mount_csv_separators_are_refused(self):
        for path in ['/private/tmp/a,b','/private/tmp/a\nb']:
            with self.assertRaises(ValueError):rea.concrete(path)

    def test_environment_credential_files_are_refused_before_content_reads(self):
        for name in ['.env','.env.local','.npmrc','.netrc']:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp).resolve();source=root/'artifact';source.mkdir();(source/name).write_text('synthetic-only')
                with patch.object(rea.os,'fdopen',side_effect=AssertionError('Sensitive content must not open')):
                    with self.assertRaises(ValueError):rea.snapshot(source,root/'snapshot')

    def test_foreign_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();src=root/'input';src.mkdir();out=root/'output';out.mkdir();(out/'work').write_bytes(b'original')
            with self.assertRaises(ValueError):rea.owned_task(root/'state',src,out)
            self.assertEqual((out/'work').read_bytes(),b'original')

    def test_tar_parent_links_and_duplicate_paths_are_rejected(self):
        for evil in ['package/../escaped','package/a']:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); archive=root/'a.tar'
                with tarfile.open(archive,'w') as t:
                    m=tarfile.TarInfo(evil);m.size=1;t.addfile(m,io.BytesIO(b'x'))
                    if evil=='package/a':
                        m=tarfile.TarInfo('package/a');m.size=1;t.addfile(m,io.BytesIO(b'y'))
                with self.assertRaises(ValueError):rea.safe_tar(archive,root/'out')
                self.assertFalse((root/'escaped').exists())

    def test_zip_symlinks_cannot_write_outside_owned_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'bad.zip'
            with zipfile.ZipFile(p,'w') as z:
                i=zipfile.ZipInfo('ghidra_12.1.4_PUBLIC/link');i.external_attr=0o120777<<16;z.writestr(i,'../../outside')
            with self.assertRaises(ValueError):rea.safe_zip(p,root/'out')

    def test_fixed_dependency_set_has_no_mutable_urls_or_extra_root(self):
        self.assertEqual(len(rea.PINS['debian_packages']),14)
        self.assertEqual(len({x['name'] for x in rea.PINS['debian_packages']}),14)
        self.assertRegex(rea.PINS['base'],r'^node@sha256:[0-9a-f]{64}$')
        for row in rea.archive_files():self.assertRegex(row['sha256'],r'^[0-9a-f]{64}$')

    def test_runtime_command_preserves_os_controls_and_limits_mounts(self):
        argv=rea.container_args('sha256:fixed',Path('/private/tmp/task'),'owned',['mcp'])
        for required in ['none','--read-only','1000:1000','ALL','no-new-privileges','256','4g']:
            self.assertIn(required,argv)
        self.assertEqual(sum(x=='--mount' for x in argv),2)
        joined=' '.join(argv)
        for disallowed in ['--privileged','--pid=host','docker.sock','/Users','seccomp=unconfined']:
            self.assertNotIn(disallowed,joined)
        self.assertIn('dst=/input,readonly',joined)

if __name__=='__main__':unittest.main()
