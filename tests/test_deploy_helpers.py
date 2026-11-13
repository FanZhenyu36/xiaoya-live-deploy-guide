import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


def module(name, path):
    spec=importlib.util.spec_from_file_location(name, path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class ConfigSafetyTests(unittest.TestCase):
    def test_existing_private_config_is_never_overwritten(self):
        m=module('configurator',ROOT/'scripts/configure_stage.py')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            stage=p/'stage'
            stage.mkdir()
            original='{"user_kept_this":true}\n'
            (stage/'config.json').write_text(original)
            self.assertFalse(m.create_config(stage,p/'runtime'))
            self.assertEqual((stage/'config.json').read_text(),original)

    def test_new_config_keeps_keys_empty_and_runtime_assets_separate(self):
        m=module('configurator',ROOT/'scripts/configure_stage.py')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            self.assertTrue(m.create_config(p/'stage',p/'private-runtime'))
            c=json.loads((p/'stage/config.json').read_text(encoding='utf-8'))
            self.assertEqual(c['vidu']['api_key'],'')
            self.assertEqual(c['avatar']['avatar_id'],'')
            self.assertIn('private-runtime',c['llm']['key_file'])
            self.assertEqual(c['rtc']['managed_recording'],False)


class ModelPathTests(unittest.TestCase):
    def test_incomplete_checkpoint_reports_required_weights(self):
        m=module('modelcheck',ROOT/'scripts/wsl/check_model.py')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/'config.json').write_text('{}')
            missing=m.validate_model(p)
            self.assertIn('model.safetensors',missing)
            self.assertIn('audio_tokenizer/model.safetensors',missing)
            with self.assertRaises(ValueError):
                m.locate_model(str(p))


class PublicationTests(unittest.TestCase):
    def test_scanner_rejects_credential_like_content_without_echoing_value(self):
        m=module('publicscan',ROOT/'scripts/scan_public_files.py')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            fake='vda_'+'x'*40
            (p/'bad.txt').write_text(fake)
            results=m.scan(p)
            self.assertTrue(results)
            self.assertNotIn(fake,'\n'.join(results))


if __name__=='__main__':
    unittest.main()
