import threading
from authority_cfg import AuthorityCfg


class Context:
    def __init__(self):
        self.lock = threading.RLock()
        self.user_list = None
        self.authority = AuthorityCfg()
        self.authority.read_config()

    @classmethod
    def instance(cls, *args, **kwargs):
        if not hasattr(cls, "ins"):
            ins_obj = cls(*args, **kwargs)
            setattr(cls, "ins", ins_obj)
        return getattr(cls, "ins")

    def set_user_list(self, data):
        self.user_list = data

    def get_user_info(self):
        try:
            self.lock.acquire()
            data = self.user_list
            self.lock.release()
            return data
        except Exception:
            self.lock.release()
            raise

    def update_authority(self):
        self.authority.read_config()

    def get_authority_cfg(self):
        return self.authority.get_authority_cfg()

