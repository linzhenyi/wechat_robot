from plugin_interface import PluginInterface, cmd_dump
from context import Context

NAME = '获取调试信息'
ARG_GROUP = '群'
ARG_USER_LIST = '好友'


class PluginImp(PluginInterface):
    def __init__(self):
        super().__init__()

    def get_name(self):
        return NAME

    def get_help(self):
        return '转存储当前相关微信数据，方便进行调试和分析问题，只有管理员身份可用。'\
               '生效后会将数据私信到发送人。具体参数如下：\n' + ARG_GROUP + '\n' + ARG_USER_LIST

    def module_load(self):
        super().module_load()

    def module_unload(self):
        super().module_unload()

    def handle_recv_msg(self, msg, wxid=None, roomid=None, nickname=None):
        super().handle_recv_msg(msg, wxid, roomid, nickname)
        if not super().is_greater_than_admin(wxid):
            super().send_msg('权限不足，请联系管理员添加权限', wxid, roomid, nickname)
            return
        if msg == ARG_GROUP:
            if roomid:
                super().send_cmd(cmd_dump, None, wxid, roomid, nickname)
            else:
                super().send_msg('该命令只能在群内使用', wxid, roomid, nickname)
        elif msg == ARG_USER_LIST:
            super().send_msg(str(Context.instance().get_user_info()), wxid, roomid, nickname)


