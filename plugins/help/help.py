from plugin_interface import PluginInterface, cmd_help

NAME = '帮助'


class PluginImp(PluginInterface):
    def __init__(self):
        super().__init__()

    def get_name(self):
        return NAME

    def get_help(self):
        return ''

    def module_load(self):
        super().module_load()

    def module_unload(self):
        super().module_unload()

    def handle_recv_msg(self, msg, wxid=None, roomid=None, nickname=None):
        super().handle_recv_msg(msg, wxid, roomid, nickname)
        if not super().is_greater_than_user(wxid):
            return
        super().send_cmd(cmd_help, msg, wxid, roomid, nickname)
