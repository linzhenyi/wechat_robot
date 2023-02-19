from context import Context

cmd_dump = 'dump'
cmd_help = 'help'
cmd_update_plugins = 'update_plugins'
cmd_update_authority = 'update_authority'


class PluginInterface:
    def __init__(self):
        self.__func_send_msg = None
        self.__func_send_cmd = None

    def init(self, func_send_msg, func_send_cmd):
        self.__func_send_msg = func_send_msg
        self.__func_send_cmd = func_send_cmd

    def get_name(self):
        return ''

    def get_help(self):
        return ''

    def module_load(self):
        pass

    def module_unload(self):
        pass

    def handle_recv_msg(self, msg, wxid=None, roomid=None, nickname=None):
        pass

    def send_msg(self, msg, wxid=None, roomid=None, nickname=None):
        self.__func_send_msg(msg, wxid, roomid, nickname)

    def send_cmd(self, cmd, arg=None, owner_wxid=None, owner_roomid=None, owner_nickname=None):
        self.__func_send_cmd(cmd, arg, owner_wxid, owner_roomid, owner_nickname)

    def is_greater_than_user(self, wxid):
        authority_cfg = Context.instance().get_authority_cfg()
        return self.is_greater_than_admin(wxid) or wxid in authority_cfg['user']

    def is_greater_than_admin(self, wxid):
        authority_cfg = Context.instance().get_authority_cfg()
        return self.is_greater_than_super_admin(wxid) or wxid in authority_cfg['admin']

    def is_greater_than_super_admin(self, wxid):
        authority_cfg = Context.instance().get_authority_cfg()
        return wxid in authority_cfg['super_admin']
