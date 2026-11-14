import asyncio
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from unittest.mock import MagicMock, AsyncMock

from src.audience import AudienceQueue
from src.engine import Engine
from src.llm import SentenceStream

spec = importlib.util.spec_from_file_location('tested_relay', Path(__import__('src').__file__).parent.parent/'tools/douyin_relay.py')
relay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(relay)


class QueueTests(unittest.TestCase):
    def test_questions_precede_welcomes_and_keep_arrival_order(self):
        q = AudienceQueue()
        q.add_welcome({'nick':'访客'})
        q.add_question({'text':'第一题'})
        q.add_question({'text':'第二题'})
        self.assertEqual([q.pop_next()[0] for _ in range(3)], ['question','question','welcome'])

    def test_full_queue_keeps_older_questions(self):
        q = AudienceQueue(question_limit=2)
        q.add_question({'text':'第一题'})
        q.add_question({'text':'第二题'})
        self.assertEqual(q.add_question({'text':'第三题'})['reason'], 'queue_full')
        self.assertEqual([q.pop_next()[1]['text'] for _ in range(2)], ['第一题','第二题'])

    def test_replayed_event_id_is_not_answered_twice(self):
        q = AudienceQueue()
        item = {'text':'问题','platform':'抖音'}
        self.assertTrue(q.add_question(item,'unique-event')['queued'])
        self.assertEqual(q.add_question(item,'unique-event')['reason'],'duplicate')

    def test_repeated_entrance_is_deduplicated_by_user(self):
        q = AudienceQueue()
        self.assertTrue(q.add_welcome({'nick':'甲'},uid='same-user')['queued'])
        self.assertFalse(q.add_welcome({'nick':'甲改名'},uid='same-user')['queued'])
        self.assertEqual(len(q.welcomes),1)

    def test_stream_does_not_stop_at_comma_when_sentence_mode_enabled(self):
        s = SentenceStream(sentence_only=True)
        self.assertEqual(s.feed('这句话还没有说完，后面还有一大段内容，'), [])
        self.assertEqual(s.feed('现在说完了。'), ['这句话还没有说完，后面还有一大段内容，现在说完了。'])


class RelayTests(unittest.TestCase):
    def test_member_event_becomes_join_without_llm_question(self):
        p = relay.to_bridge_payload({'method':'WebcastMemberMessage','user':{'id':'123','nickname':'新朋友'}})
        self.assertEqual(p['kind'],'join')
        self.assertEqual(p['uid'],'123')
        self.assertIn('新朋友',p['text'])

    def test_chat_keeps_event_id_and_requests_answer_only(self):
        p = relay.to_bridge_payload({'method':'WebcastChatMessage','common':{'msgId':'10001'},'user':{'nickname':'甲'},'content':'你好？'})
        self.assertEqual(p['event_id'],'10001')
        self.assertTrue(p['answer_only'])

    def test_follow_and_anonymous_member_are_not_spoken(self):
        self.assertIsNone(relay.to_bridge_payload({'method':'WebcastSocialMessage','user':{'nickname':'甲'}}))
        self.assertIsNone(relay.to_bridge_payload({'method':'WebcastMemberMessage','user':{}}))


class RouteTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        config_patch = patch('src.config.load',return_value={})
        config_patch.start()
        self.addCleanup(config_patch.stop)

    async def test_member_reaches_welcome_route_and_never_action_or_chat_route(self):
        import httpx
        from src import bridge
        fake = MagicMock()
        fake.enqueue_welcome.return_value = {'ok':True,'queued':True,'reason':'welcome'}
        with patch.object(bridge,'engine',fake), patch.object(bridge.dm_router,'enqueue') as actions:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=bridge.app),base_url='http://test') as client:
                r = await client.post('/api/danmaku',json={'kind':'join','nick':'新朋友','uid':'u1','platform':'抖音'})
            self.assertEqual(r.status_code,200)
            fake.enqueue_welcome.assert_called_once_with('新朋友',uid='u1',platform='抖音')
            fake.enqueue_danmaku.assert_not_called()
            actions.assert_not_called()

    async def test_chat_content_and_event_id_are_kept(self):
        import httpx
        from src import bridge
        fake = MagicMock()
        fake.enqueue_danmaku.return_value = {'ok':True,'queued':True,'reason':'fifo'}
        with patch.object(bridge,'engine',fake), patch.object(bridge.dm_router,'enqueue'), patch.object(bridge.dm_router,'looks_like_cmd',return_value=False):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=bridge.app),base_url='http://test') as client:
                r = await client.post('/api/danmaku',json={'content':'第一题','nick':'甲','event_id':'e1'})
            self.assertEqual(r.status_code,200)
            self.assertEqual(fake.enqueue_danmaku.call_args.args[0],'第一题')
            self.assertEqual(fake.enqueue_danmaku.call_args.kwargs['event_id'],'e1')


class FakeSignal:
    def __init__(self):
        self.interrupts = 0
        self.texts = []

    async def send_output_text(self,text):
        self.texts.append(text)

    async def interrupt(self):
        self.interrupts += 1


class FakeTTS:
    async def synth_pcm(self,text,preset):
        return bytes(960)


class FakeLLM:
    def __init__(self):
        self.prompts = []

    async def stream(self,text,record=True):
        self.prompts.append(text)
        label = '第一题' if '第一题' in text else '第二题'
        yield label+'的完整回答。'


class EngineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.conf = {'danmaku':{'queue_mode':'fifo','read_interval_ms':0,'batch':{'enabled':False}},
                     'session':{'finish_sentence_before_interrupt':True}, 'tts':{}}
        self.patcher = patch.multiple('src.engine.appconf',load=lambda:self.conf,reload=lambda:self.conf)
        self.patcher.start()
        self.e = Engine()
        self.e.phase = 'live'
        self.e.sig = FakeSignal()
        self.e.tts = FakeTTS()
        self.e.llm = FakeLLM()
        self.e._voice_preset = lambda: {}
        self.played = []

        async def feed(pcm,evt,events=None):
            self.played.append(self.e.speaking_text)
            await asyncio.sleep(0)
            return True
        self.e._feed_pcm_stream = feed

    async def asyncTearDown(self):
        self.e.phase = 'idle'
        tasks = [t for t in (self.e._dan_task,self.e._speak_task,self.e._pending_interrupt) if t and not t.done()]
        for task in tasks: task.cancel()
        if tasks: await asyncio.gather(*tasks,return_exceptions=True)
        self.patcher.stop()

    async def test_vip_question_does_not_overtake_older_question_or_trigger_welcome(self):
        self.e.enqueue_welcome('新朋友')
        self.e.enqueue_danmaku('第一题',nick='甲',content='第一题')
        self.e.enqueue_danmaku('第二题',priority='vip',nick='乙',content='第二题')
        await asyncio.wait_for(self.e._dan_task,2)
        self.assertEqual(self.played[:2],['甲，第一题的完整回答。','乙，第二题的完整回答。'])
        self.assertIn('欢迎新朋友',self.played[2])

    async def test_question_arriving_during_welcome_synthesis_is_played_first(self):
        started,release = asyncio.Event(),asyncio.Event()

        class SlowWelcome:
            async def synth_pcm(inner,text,preset):
                if text.startswith('欢迎'):
                    started.set()
                    await release.wait()
                return bytes(960)
        self.e.tts = SlowWelcome()
        self.e.enqueue_welcome('新朋友')
        worker = self.e._dan_task
        await asyncio.wait_for(started.wait(),1)
        self.e.enqueue_danmaku('第一题',nick='甲',content='第一题')
        release.set()
        await asyncio.wait_for(worker,2)
        self.assertEqual(self.played[0],'甲，第一题的完整回答。')
        self.assertIn('欢迎新朋友',self.played[1])

    async def test_join_is_displayed_once_and_not_answered_by_llm(self):
        self.e.enqueue_welcome('新朋友',uid='u1')
        self.e.enqueue_welcome('新朋友',uid='u1')
        await asyncio.wait_for(self.e._dan_task,2)
        joins = [x for x in self.e.transcripts if x['role']=='join']
        self.assertEqual(len(joins),1)
        self.assertEqual(self.e.llm.prompts,[])

    async def test_nickname_and_first_answer_share_one_audio_chunk_without_reading_question(self):
        async def answer(text,record=True):
            yield '记得早点休息。也可以喝点水。'
        self.e.llm.stream = answer
        self.e.enqueue_danmaku('怎样保持精力？',nick='小明',content='怎样保持精力？')
        await asyncio.wait_for(self.e._dan_task,2)
        self.assertEqual(self.played,['小明，记得早点休息。','也可以喝点水。'])
        self.assertNotIn('怎样保持精力', ''.join(self.played))

    async def test_model_address_is_not_repeated(self):
        async def answer(text,record=True):
            yield '小明，你可以先休息一下。'
        self.e.llm.stream = answer
        self.e.enqueue_danmaku('好累怎么办？',nick='小明',content='好累怎么办？')
        await asyncio.wait_for(self.e._dan_task,2)
        self.assertEqual(self.played,['小明，你可以先休息一下。'])

    async def test_missing_nickname_does_not_read_account_id(self):
        self.e.enqueue_danmaku('第一题',content='第一题')
        await asyncio.wait_for(self.e._dan_task,2)
        self.assertEqual(self.played,['第一题的完整回答。'])

    async def test_nickname_prefix_does_not_confuse_word_with_address(self):
        self.assertEqual(self.e._dan_answer_with_nick(['小时候也要按时休息。'],{'nick':'小'}),
                         ['小，小时候也要按时休息。'])

    async def test_nickname_control_characters_are_removed(self):
        self.assertEqual(self.e._dan_answer_with_nick(['可以呀。'],{'nick':'小\n明\u202e'}),
                         ['小明，可以呀。'])

    async def test_interrupt_waits_for_current_sentence_and_never_sends_clear_buffer(self):
        started,release = asyncio.Event(),asyncio.Event()

        async def feed(pcm,evt,events=None):
            self.played.append(self.e.speaking_text)
            started.set()
            await release.wait()
            return True
        self.e._feed_pcm_stream = feed
        victim = asyncio.create_task(self.e._safe_say_text('第一句话。第二句话。'))
        self.e._speak_task = victim
        await asyncio.wait_for(started.wait(),1)
        reply = await self.e.interrupt()
        self.assertTrue(reply['deferred'])
        await asyncio.sleep(0)
        self.assertFalse(victim.done())
        release.set()
        await asyncio.wait_for(self.e._pending_interrupt,1)
        self.assertEqual(len(self.played),1)
        self.assertEqual(self.e.sig.interrupts,0)

    async def test_higher_priority_task_waits_until_old_sentence_finishes(self):
        started,release = asyncio.Event(),asyncio.Event()

        async def feed(pcm,evt,events=None):
            started.set()
            await release.wait()
            return True
        self.e._feed_pcm_stream = feed

        async def owner():
            await self.e._own_audio()
            try: await self.e._feed_pcm(bytes(960),asyncio.Event())
            finally: self.e._release_audio()

        victim = asyncio.create_task(owner())
        await started.wait()

        async def next_owner():
            await self.e._own_audio(preempt=True)
            self.e._release_audio()
        next_task = asyncio.create_task(next_owner())
        await asyncio.sleep(0)
        self.assertFalse(next_task.done())
        release.set()
        await asyncio.wait_for(asyncio.gather(victim,next_task),1)
        self.assertEqual(self.e.sig.interrupts,0)

    async def test_background_audio_cannot_claim_idle_slot_while_question_is_generating(self):
        self.e._dan_current_kind = 'question'
        task = asyncio.create_task(self.e._own_audio(preempt=False,wait_only=True,defer_to_questions=True))
        await asyncio.sleep(.02)
        self.assertFalse(task.done())
        self.e._dan_current_kind = ''
        self.assertTrue(await asyncio.wait_for(task,1))

    async def test_question_takes_over_background_only_after_current_sentence(self):
        started,release = asyncio.Event(),asyncio.Event()
        async def feed(pcm,evt,events=None):
            self.played.append('background sentence')
            started.set()
            await release.wait()
            return True
        self.e._feed_pcm_stream = feed
        async def background():
            await self.e._own_audio(defer_to_questions=True)
            try:
                for _ in range(2):
                    if not await self.e._feed_pcm(bytes(960),asyncio.Event()):
                        return
            finally:
                self.e._release_audio()
        victim = asyncio.create_task(background())
        await asyncio.wait_for(started.wait(),1)
        self.e._dan_current_kind = 'question'
        async def question():
            await self.e._own_audio(preempt=True,wait_only=True)
            self.e._release_audio()
        next_task = asyncio.create_task(question())
        await asyncio.sleep(.01)
        self.assertFalse(next_task.done())
        release.set()
        await asyncio.wait_for(asyncio.gather(victim,next_task,return_exceptions=True),1)
        self.assertEqual(self.played,['background sentence'])
        self.assertEqual(self.e.sig.interrupts,0)


if __name__=='__main__':
    unittest.main()
