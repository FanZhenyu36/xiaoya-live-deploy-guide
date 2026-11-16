import unittest
from unittest.mock import patch
from src.llm import LLMClient
from src.engine import Engine
from test_audience_queue import FakeSignal

class BroadcastRuleTests(unittest.TestCase):
    def test_global_persona_kept_with_broadcast_rules(self):
        c=LLMClient(lambda:{'system_prompt':'你是小肉包，六岁，爸爸是路飞。'})
        with patch('src.personas.active_prompt',return_value=None):p=c.system_prompt()
        self.assertTrue(p.startswith('你是小肉包，六岁，爸爸是路飞。'))
        self.assertIn('只有主播通过界面结束连线',p)
        self.assertIn('视为过时的错误剧情',p)
    def test_selected_persona_receives_same_guard(self):
        c=LLMClient(lambda:{'system_prompt':'旧全局','persona':'test'})
        with patch('src.personas.active_prompt',return_value='独立人设'):p=c.system_prompt()
        self.assertTrue(p.startswith('独立人设'));self.assertNotIn('旧全局',p)
        self.assertIn('不得主动声称自己要睡觉',p)
    def test_viewer_can_still_say_goodnight(self):
        c=LLMClient(lambda:{'system_prompt':'人设'})
        c.history.append({'role':'assistant','content':'之前说要下播的旧剧情'})
        with patch('src.personas.active_prompt',return_value=None):messages=c._messages('我要睡觉了，晚安')
        self.assertEqual(messages[-1]['content'],'我要睡觉了，晚安')
        self.assertIn('可以祝对方晚安',messages[0]['content'])
        self.assertIn('自己仍继续直播',messages[0]['content'])
    def test_opt_out_preserves_original_prompt(self):
        c=LLMClient(lambda:{'system_prompt':'原人设','broadcast_rules_enabled':False})
        with patch('src.personas.active_prompt',return_value=None):self.assertEqual(c.system_prompt(),'原人设')
    def test_reset_clears_only_conversation_memory(self):
        conf={'system_prompt':'原人设'};c=LLMClient(lambda:conf)
        c.history.append({'role':'assistant','content':'要睡觉啦'})
        c.reset_history();self.assertFalse(c.history);self.assertEqual(conf,{'system_prompt':'原人设'})

class IdlePromptTests(unittest.IsolatedAsyncioTestCase):
    async def test_idle_topics_do_not_ask_bedtime_or_invent_drowsiness(self):
        conf={'session':{},'tts':{}}
        with patch.multiple('src.engine.appconf',load=lambda:conf,reload=lambda:conf):
            e=Engine();e.phase='live';e.sig=FakeSignal();prompts=[]
            async def collect(text,record=True):prompts.append(text);return []
            e._llm_collect=collect;e._idle_turn=1
            await e._idle_say(30);await e._idle_say(30)
        self.assertIn('喜欢什么小吃',prompts[0]);self.assertNotIn('几点睡',prompts[0])
        self.assertIn('直播仍在继续',prompts[0]);self.assertIn('不编造自己困倦',prompts[1])

if __name__=='__main__':unittest.main()
