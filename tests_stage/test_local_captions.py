import asyncio
import unittest
from unittest.mock import patch
from src.engine import Engine
from test_audience_queue import FakeSignal,FakeTTS

class LocalCaptionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.conf={'session':{'send_output_text_to_vidu':False,'finish_sentence_before_interrupt':True},'tts':{}}
        self.p=patch.multiple('src.engine.appconf',load=lambda:self.conf,reload=lambda:self.conf)
        self.p.start();self.addCleanup(self.p.stop)
        self.e=Engine();self.e.phase='live';self.e.sig=FakeSignal();self.e.tts=FakeTTS()
        self.e._voice_preset=lambda:{};self.played=[]
        async def feed(pcm,evt,events=None):
            self.played.append(self.e.speaking_text);return True
        self.e._feed_pcm_stream=feed

    async def test_local_subtitle_and_audio_survive_when_cloud_text_disabled(self):
        await self.e._safe_say_text('小明，你好。')
        self.assertEqual(self.played,['小明，你好。'])
        self.assertEqual(self.e.sig.texts,[])
        self.assertTrue(any(x['role']=='dh' and x['text']=='小明，你好。' for x in self.e.transcripts))

    async def test_cloud_context_can_be_restored(self):
        self.conf['session']['send_output_text_to_vidu']=True
        self.assertTrue(await self.e._out_text('你好。'))
        self.assertEqual(self.e.sig.texts,['你好。'])

    async def test_legacy_default_preserves_cloud_context(self):
        self.conf['session'].pop('send_output_text_to_vidu')
        self.assertTrue(await self.e._out_text('你好。'))
        self.assertEqual(self.e.sig.texts,['你好。'])

    async def test_disabled_text_does_not_hide_disconnected_session(self):
        self.e.phase='idle'
        self.assertFalse(await self.e._out_text('你好。'))

if __name__=='__main__':unittest.main()
