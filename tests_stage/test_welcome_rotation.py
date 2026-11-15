import asyncio,unittest
from unittest.mock import patch
from src.audience import WelcomeRotation,DEFAULT_WELCOME_TEMPLATES
from src.engine import Engine
from test_audience_queue import FakeSignal,FakeTTS

class RotationTests(unittest.TestCase):
    def test_eight_phrases_rotate_then_wrap(self):
        r=WelcomeRotation();lines=[r.next('小明') for _ in range(9)]
        self.assertEqual(len(set(lines[:8])),8);self.assertEqual(lines[0],lines[8])
        self.assertTrue(all('小明' in line for line in lines))
    def test_custom_phrases_keep_nickname(self):
        r=WelcomeRotation();self.assertEqual(r.next('小明',['欢迎{nick}。','进来坐坐。']),'欢迎小明。')
        self.assertEqual(r.next('小红',['欢迎{nick}。','进来坐坐。']),'小红，进来坐坐。')
    def test_invalid_configuration_falls_back(self):
        for value in (None,[],[None,3,' '],'not-a-list'):
            self.assertEqual(WelcomeRotation().next('甲',value),DEFAULT_WELCOME_TEMPLATES[0].replace('{nick}','甲'))
    def test_nickname_braces_are_literal(self):
        self.assertEqual(WelcomeRotation().next('{name}',['欢迎{nick}。']),'欢迎{name}。')

class WelcomeCacheTests(unittest.IsolatedAsyncioTestCase):
    async def test_question_deferral_preserves_text_pcm_and_rotation_position(self):
        conf={'session':{'finish_sentence_before_interrupt':True},'danmaku':{'queue_mode':'fifo'},'tts':{}}
        with patch.multiple('src.engine.appconf',load=lambda:conf,reload=lambda:conf):
            e=Engine();e.phase='live';e.sig=FakeSignal();e.tts=FakeTTS();e._voice_preset=lambda:{}
            calls=[];played=[]
            async def synth(text,preset):calls.append(text);return bytes(960)
            async def feed(*args,**kwargs):played.append(e.speaking_text);return True
            e.tts.synth_pcm=synth;e._feed_pcm_stream=feed
            flags=iter([False,True]);e._questions_waiting=lambda:next(flags)
            item={'nick':'新朋友'};await e._speak_welcome_item(item)
            self.assertEqual(len(e._welcome_q),1);self.assertEqual(e._welcome_rotation.turn,1)
            e._questions_waiting=lambda:False
            await e._speak_welcome_item(e._welcome_q.popleft())
            self.assertEqual(calls,played);self.assertEqual(len(calls),1)
            self.assertEqual(e._welcome_rotation.turn,1)

if __name__=='__main__':unittest.main()
