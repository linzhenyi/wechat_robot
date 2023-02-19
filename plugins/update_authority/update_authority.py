from plugin_interface import PluginInterface, cmd_update_authority

NAME = '更新权限'


class PluginImp(PluginInterface):
    def __init__(self):
        super().__init__()

    def get_name(self):
        return NAME

    def get_help(self):
        return '配置权限文件后使用该命令热更新'

    def module_load(self):
        super().module_load()

    def module_unload(self):
        super().module_unload()

    def handle_recv_msg(self, msg, wxid=None, roomid=None, nickname=None):
        super().handle_recv_msg(msg, wxid, roomid, nickname)
        if not super().is_greater_than_admin(wxid):
            return
        super().send_cmd(cmd_update_authority, msg, wxid, roomid, nickname)
