from plugin_interface import PluginInterface, cmd_update_plugins

NAME = '更新插件'


class PluginImp(PluginInterface):
    def __init__(self):
        super().__init__()

    def get_name(self):
        return NAME

    def get_help(self):
        return '热更新插件，可新增，删除，修改。修改时需要加具体参数为：' + NAME + ' 插件名称'

    def module_load(self):
        super().module_load()

    def module_unload(self):
        super().module_unload()

    def handle_recv_msg(self, msg, wxid=None, roomid=None, nickname=None):
        super().handle_recv_msg(msg, wxid, roomid, nickname)
        if not super().is_greater_than_admin(wxid):
            return
        super().send_cmd(cmd_update_plugins, msg, wxid, roomid, nickname)
