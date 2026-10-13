import json
from pathlib import Path
import tempfile
import unittest
from effortless_codex.install import install_files

class InstallTests(unittest.TestCase):
    def test_installs_runtime_launcher_skill_and_restore_record(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)
            result=install_files(home,'/python','/codex-main','/codex-judge','gpt-6.1-sol',previous_override='/original')
            config=json.loads(Path(result['config']).read_text())
            self.assertEqual(config['judge_model'],'gpt-6.1-sol')
            self.assertTrue(config['auto'])
            self.assertEqual(config['previous_override'],'/original')
            self.assertTrue((home/'.codex/skills/effortless-codex/SKILL.md').exists())
            self.assertTrue((home/'.local/share/effortless-codex/app/effortless_codex/proxy.py').exists())
            self.assertTrue(Path(result['launcher']).stat().st_mode & 0o111)

    def test_does_not_overwrite_an_unrelated_launcher(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td);p=home/'.local/bin/effortless-codex';p.parent.mkdir(parents=True)
            p.write_text('user-owned command')
            with self.assertRaises(FileExistsError):install_files(home,'/python','/main','/judge','gpt-6.1-sol')
            self.assertEqual(p.read_text(),'user-owned command')

    def test_unrelated_login_service_is_checked_before_any_files_are_written(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td);p=home/'Library/LaunchAgents/local.effortless-codex.environment.plist'
            p.parent.mkdir(parents=True);p.write_text('user-owned service')
            with self.assertRaises(FileExistsError):install_files(home,'/python','/main','/judge','gpt-6.1-sol')
            self.assertFalse((home/'.local/bin/effortless-codex').exists())
            self.assertEqual(p.read_text(),'user-owned service')

if __name__=='__main__':unittest.main()
