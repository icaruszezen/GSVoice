import base64
from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *
from pkg.command import entities
from pkg.command.operator import CommandOperator, operator_class
from pkg.platform.types import MessageChain, Plain, Voice
from .pkg.utils.text_cleaner import clean_markdown
import os
import json
import yaml
import requests

# 注册插件
@register(name="GSVoice语音对话生成", description="沉浸式角色扮演聊天，使用GPT-SoVits生成语音对话", version="0.1", author="球球")
class GSVoicePlugin(BasePlugin):

    # 插件初始化
    def __init__(self, host: APIHost):
        super().__init__(host)
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        self.api_url = config['api_url']

    async def generate_audio(self,character,text):
        url = self.api_url + "/character"  # 替换为实际接口地址

        payload = {
            "character": character,
            "text": text,
            "text_language": "zh",
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }


        response = requests.post(
            url,
            data=json.dumps(payload),
            headers=headers
        )

        # 检查响应状态
        if response.status_code == 200:
            print("请求成功！")
            with open('./output.wav', 'wb') as f:
                f.write(response.content)
            print("音频文件已保存为：./output.wav")
            return "./output.wav"
        else:
            print(f"请求失败，状态码：{response.status_code}")
            print("错误信息：", response.text)
            return None


    # 处理发送的消息
    @handler(NormalMessageResponded)
    async def handle_message(self, ctx: EventContext):
        #处理消息
        # 清理Markdown格式并生成语音
        text = clean_markdown(ctx.event.response_text)

        try:
            audio_path = await self.generate_audio("Amiya", text)
            if audio_path is None:  # 文本过长或生成失败
                return

            # 构建消息链
            message_elements = []

            # 使用Voice消息发送
            with open(audio_path, "rb") as f:
                base64_audio = base64.b64encode(f.read()).decode()
            message_elements.append(Voice(base64=base64_audio))

            # 构建消息链并发送
            if message_elements:
                msg_chain = MessageChain(message_elements)
                await ctx.reply(msg_chain)
        except Exception as e:
            print(f"生成语音失败: {e}")
            return
        finally:
            # 清理临时文件
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception as e:
                    print(f"清理临时文件失败: {e}")

# 插件卸载时触发
    def __del__(self):
        pass