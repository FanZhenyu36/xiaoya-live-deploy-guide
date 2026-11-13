import unittest
from src.engine import Engine
from src.llm import merge_for_tts


class FakeLLM:
    def __init__(self, chunks):
        self.chunks = chunks

    async def stream(self, text, record=True):
        for chunk in self.chunks:
            yield chunk


class CollectedSpeechTests(unittest.IsolatedAsyncioTestCase):
    async def collect(self, *chunks):
        engine = Engine.__new__(Engine)
        engine.llm = FakeLLM(chunks)
        return await engine._llm_collect('test')

    async def test_unpunctuated_tail_is_one_sentence(self):
        result = await self.collect('你好，今天我们接着聊～')
        self.assertEqual(result, ['你好，今天我们接着聊～'])

    async def test_two_sentence_limit_keeps_full_reply_after_commas(self):
        text = '朋友你好，这个嘛，先保密，你猜猜看～'
        result = await self.collect('朋友你好，这个嘛，', '先保密，你猜猜看～')
        self.assertEqual(''.join(result[:2]), text)

    async def test_real_sentence_boundaries_are_preserved(self):
        result = await self.collect('你好，今天很开心。', '明天继续聊，你记得来。', '再见～')
        self.assertEqual(result, ['你好，今天很开心。', '明天继续聊，你记得来。', '再见～'])

    async def test_stream_chunk_spaces_are_not_deleted(self):
        result = await self.collect('Hello', ' ', 'world', '!')
        self.assertEqual(result, ['Hello world!'])


class SpeechChunkTests(unittest.TestCase):
    def test_tiny_tail_is_preserved_without_extra_synthesis(self):
        first = '这是已经达到首块合成长度的一句话'
        self.assertEqual(merge_for_tts([first, '再见～']), [first + '再见～'])

    def test_long_tail_keeps_prefetch_chunks(self):
        first = '这是已经达到首块合成长度的一句话'
        tail = '这是另一段足够长的完整回答'
        chunks = merge_for_tts([first, tail])
        self.assertEqual(''.join(chunks), first + tail)
        self.assertEqual(len(chunks), 2)


if __name__ == '__main__':
    unittest.main()
