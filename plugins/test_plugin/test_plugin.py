import threading
from plugin_interface import PluginInterface

NAME = '测试'
timer_elapse = 10


class PluginImp(PluginInterface):
    def __init__(self):
        super().__init__()
        self.count = None
        self.lock = threading.RLock()
        self.timer = threading.Timer(timer_elapse, self.__timer_send)

    def get_name(self):
        return NAME

    def get_help(self):
        return '测试模块'

    def module_load(self):
        super().module_load()
        self.count = 0
        #self.timer.start()

    def module_unload(self):
        self.lock.acquire()
        #self.timer.stop()
        self.lock.release()
        super().module_unload()

    def handle_recv_msg(self, msg, wxid=None, roomid=None, nickname=None):
        super().handle_recv_msg(msg, wxid, roomid, nickname)
        #if nickname == '你自己的wechat昵称':
        #    super().send_msg(msg, None, roomid, nickname)

    def __timer_send(self):
        try:
            self.lock.acquire()
            self.timer = threading.Timer(timer_elapse, self.__timer_send)
            self.timer.start()
            self.count = self.count + 1
            super().send_msg(str(self.count), '你自己的wechat id', '群wechat id', '你自己的wechat昵称')
            self.lock.release()
        except Exception:
            self.lock.release()
            raise
