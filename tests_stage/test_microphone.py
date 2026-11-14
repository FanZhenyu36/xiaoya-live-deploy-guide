import asyncio,time,unittest
from unittest.mock import patch,AsyncMock
from src.engine import Engine
from test_audience_queue import FakeSignal,FakeTTS,FakeLLM

class MicrophoneTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.conf={'session':{'finish_sentence_before_interrupt':True},'danmaku':{'queue_mode':'fifo'},'tts':{}}
        self.p=patch.multiple('src.engine.appconf',load=lambda:self.conf,reload=lambda:self.conf);self.p.start();self.addCleanup(self.p.stop)
        self.e=Engine();self.e.phase='live';self.e.sig=FakeSignal();self.e.sig.send_input_text=AsyncMock()
        self.e.llm=FakeLLM();self.e.llm.trim_history=lambda:None
        self.tasks=[]
    async def asyncTearDown(self):
        self.e.phase='idle';self.e._mic_token=''
        for t in self.tasks+[self.e._mic_reply_task]:
            if t and not t.done():t.cancel()
        await asyncio.gather(*(t for t in self.tasks+[self.e._mic_reply_task] if t),return_exceptions=True)
    async def test_recording_reserves_audio_ahead_of_background_tasks(self):
        reservation=await self.e.begin_microphone()
        async def background():
            await self.e._own_audio();self.e._release_audio()
        t=asyncio.create_task(background());self.tasks.append(t)
        await asyncio.sleep(.02);self.assertFalse(t.done())
        self.e.cancel_microphone(reservation['token']);await asyncio.wait_for(t,1)
    async def test_microphone_waits_for_sentence_without_clearing_tail(self):
        started,release=asyncio.Event(),asyncio.Event()
        async def feed(*args,**kwargs):started.set();await release.wait();return True
        self.e._feed_pcm_stream=feed
        async def old():
            await self.e._own_audio()
            try:await self.e._feed_pcm(bytes(960),asyncio.Event())
            finally:self.e._release_audio()
        t=asyncio.create_task(old());self.tasks.append(t);await started.wait()
        b=asyncio.create_task(self.e.begin_microphone());self.tasks.append(b)
        await asyncio.sleep(.02);self.assertFalse(b.done());release.set()
        await asyncio.wait_for(b,1);self.assertEqual(self.e.sig.interrupts,0)
    async def test_microphone_stops_song_and_takes_highest_priority(self):
        started=asyncio.Event()
        async def song():
            await self.e._own_audio()
            self.e._song_playing=True;started.set()
            try:await asyncio.Event().wait()
            finally:self.e._release_audio()
        t=asyncio.create_task(song());self.tasks.append(t);await started.wait()
        await self.e.begin_microphone()
        self.assertTrue(t.done());self.assertFalse(self.e._song_playing);self.assertEqual(self.e.sig.interrupts,1)
    async def test_lower_priority_cannot_barge_in_on_voice_reply(self):
        r=await self.e.begin_microphone();self.e._finish_audio_owner=AsyncMock()
        self.e._audio_owner=asyncio.create_task(asyncio.sleep(20));self.tasks.append(self.e._audio_owner)
        await self.e._barge_in();self.e._finish_audio_owner.assert_not_awaited()
    async def test_stale_cancel_cannot_release_new_recording(self):
        r=await self.e.begin_microphone();self.e.cancel_microphone('old-token')
        self.assertTrue(self.e._mic_priority_active())
        self.e.cancel_microphone(r['token']);self.assertFalse(self.e._mic_priority_active())
    async def test_cancelled_audio_cannot_be_sent_as_chat(self):
        r=await self.e.begin_microphone();self.e.cancel_microphone(r['token'])
        with self.assertRaises(RuntimeError):await self.e.chat('你好',mic_token=r['token'])
        self.e.sig.send_input_text.assert_not_awaited()
    async def test_voice_reply_keeps_priority_until_it_finishes(self):
        entered,release=asyncio.Event(),asyncio.Event()
        async def speak(text):entered.set();await release.wait()
        self.e._speak_llm=speak
        r=await self.e.begin_microphone();await self.e.chat('你好',mic_token=r['token']);await entered.wait()
        self.assertTrue(self.e._mic_priority_active())
        with self.assertRaises(RuntimeError):await self.e.chat('别插队')
        release.set();await asyncio.wait_for(self.e._mic_reply_task,1)
        self.assertFalse(self.e._mic_priority_active())
    async def test_expired_abandoned_recording_releases_priority(self):
        await self.e.begin_microphone();self.e._mic_deadline=time.monotonic()-1
        self.assertFalse(self.e._mic_priority_active())
    async def test_danmaku_waits_while_microphone_records(self):
        r=await self.e.begin_microphone();t=asyncio.create_task(self.e._dan_hold_gates());self.tasks.append(t)
        await asyncio.sleep(.02);self.assertFalse(t.done())
        self.e.cancel_microphone(r['token']);self.assertTrue(await asyncio.wait_for(t,1))
    async def test_idle_session_cannot_record(self):
        self.e.phase='idle'
        with self.assertRaises(RuntimeError):await self.e.begin_microphone()

if __name__=='__main__':unittest.main()

class MicrophoneRouteTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        p=patch('src.config.load',return_value={});p.start();self.addCleanup(p.stop)
    async def test_transcribed_audio_reaches_high_priority_chat(self):
        import httpx
        from src import bridge
        from unittest.mock import MagicMock
        fake=MagicMock();fake.chat=AsyncMock(return_value={'ok':True})
        proxy=MagicMock();proxy.post=AsyncMock(return_value=httpx.Response(200,json={'text':'你好'}))
        manager=MagicMock();manager.__aenter__=AsyncMock(return_value=proxy);manager.__aexit__=AsyncMock(return_value=None)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=bridge.app),base_url='http://test') as client:
            with patch.object(bridge,'engine',fake),patch.object(bridge.httpx,'AsyncClient',return_value=manager):
                r=await client.post('/api/mic/audio',content=b'valid-audio',headers={'X-Mic-Token':'token'})
        self.assertEqual(r.status_code,200);fake.chat.assert_awaited_once_with('你好',mic_token='token')
        self.assertEqual(fake.check_microphone.call_count,2)
    async def test_cancelled_session_does_not_start_a_reply(self):
        import httpx
        from src import bridge
        from unittest.mock import MagicMock
        fake=MagicMock();fake.check_microphone.side_effect=RuntimeError('cancelled');fake.chat=AsyncMock()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=bridge.app),base_url='http://test') as client:
            with patch.object(bridge,'engine',fake):
                r=await client.post('/api/mic/audio',content=b'audio',headers={'X-Mic-Token':'old'})
        self.assertEqual(r.status_code,409);fake.chat.assert_not_awaited()
    async def test_empty_audio_releases_reservation(self):
        import httpx
        from src import bridge
        from unittest.mock import MagicMock
        fake=MagicMock();fake.chat=AsyncMock()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=bridge.app),base_url='http://test') as client:
            with patch.object(bridge,'engine',fake):
                r=await client.post('/api/mic/audio',content=b'',headers={'X-Mic-Token':'token'})
        self.assertEqual(r.status_code,413);fake.cancel_microphone.assert_called_once_with('token')
