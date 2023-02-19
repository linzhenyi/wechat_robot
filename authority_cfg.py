import json


class AuthorityCfg:
    def __init__(self):
        self.authority_cfg = None

    def read_config(self):
        with open('config/authority_cfg.json', 'r', encoding='utf-8') as f:
            self.authority_cfg = json.load(f)

    def get_authority_cfg(self):
        return self.authority_cfg
