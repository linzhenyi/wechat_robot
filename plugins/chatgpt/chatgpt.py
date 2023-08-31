import openai
from plugin_interface import PluginInterface

NAME = 'chatgpt'
openai.api_key = "你自己的key"
gpt_model = "gpt-3.5-turbo"


class PluginImp(PluginInterface):
    def __init__(self):
        super().__init__()

    def get_name(self):
        return NAME

    def get_help(self):
        return 'chatgpt模块'

    def module_load(self):
        super().module_load()

    def module_unload(self):
        super().module_unload()

    def handle_recv_msg(self, msg, wxid=None, roomid=None, nickname=None):
        super().handle_recv_msg(msg, wxid, roomid, nickname)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": msg}]
        )
        super().send_msg(response["choices"][0]["message"]["content"], wxid, roomid, nickname)

