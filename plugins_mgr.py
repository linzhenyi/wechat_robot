import importlib
import os
import sys
import traceback

class_plugin_imp_name = 'PluginImp'
func_init_name = 'init'
func_get_name = 'get_name'
func_get_help = 'get_help'
func_load_name = 'module_load'
func_unload_name = 'module_unload'
func_handle_recv_msg_name = 'handle_recv_msg'
func_send_msg_name = 'send_msg'


class PluginsMgr:
    def __init__(self):
        self.func_send_msg = None
        self.func_send_cmd = None
        self.plugins = {}

    def init(self, func_send_msg, func_send_cmd):
        self.func_send_msg = func_send_msg
        self.func_send_cmd = func_send_cmd
        self.__load_plugins()

    def handle_recv_msg(self, msg, wxid=None, roomid=None, nickname=None):
        find_index = msg.find(' ')
        if find_index == -1:
            msg_plugin = msg
            msg_content = ''
        else:
            msg_plugin = msg[0: find_index]
            msg_content = msg[find_index + 1:]
        for item in self.plugins.keys():
            if self.__call_func(item, func_get_name) == msg_plugin:
                self.__call_func(item, func_handle_recv_msg_name, msg_content, wxid, roomid, nickname)
                break

    def get_plugins_name(self):
        ret = ''
        for item in self.plugins.keys():
            name = self.__call_func(item, func_get_name)
            if name:
                ret = ret + name + '\n'
        return ret

    def get_help_txt(self, plugin):
        for item in self.plugins.keys():
            if self.__call_func(item, func_get_name) == plugin:
                return self.__call_func(item, func_get_help)
        return '无此模块'

    def update_plugins(self, plugin_name):
        if plugin_name:
            for item in self.plugins.keys():
                if self.__call_func(item, func_get_name) == plugin_name:
                    self.__call_func(item, func_unload_name)
                    del sys.modules[item]
                    self.plugins.pop(item)
                    break
        return self.__load_plugins()

    def __call_func(self, module_name, func_name, *args):
        try:
            class_type = self.plugins[module_name][0]
            class_obj = self.plugins[module_name][1]
            func_obj = getattr(class_type, func_name)
            new_args = (class_obj,) + args
            return func_obj(*new_args)
        except Exception as e:
            print(e)
            traceback.print_exc()
            return None

    def __load_plugins(self):
        try:
            new_plugins = {}
            plugins_dir = 'plugins'
            files_group = os.walk(plugins_dir)
            for path, dir_list, file_list in files_group:
                for dir_name in dir_list:
                    if dir_name[0: 2] == '__':
                        continue
                    plugin_name = dir_name
                    plugin_path = plugins_dir + '.' + dir_name + '.' + plugin_name
                    new_plugins[plugin_path] = importlib.import_module(plugin_path)

            del_plugins = self.plugins.keys() - new_plugins.keys()
            for del_item in del_plugins:
                if del_item in sys.modules:
                    self.__call_func(del_item, func_unload_name)
                    del sys.modules[del_item]
            for del_item in del_plugins:
                self.plugins.pop(del_item)

            add_plugins = new_plugins.keys() - self.plugins.keys()
            for add_item in add_plugins:
                module = importlib.import_module(add_item)
                class_type = getattr(module, class_plugin_imp_name)
                class_obj = class_type()
                self.plugins[add_item] = class_type, class_obj
                self.__call_func(add_item, func_init_name, self.func_send_msg, self.func_send_cmd)
                self.__call_func(add_item, func_load_name)
            return '更新成功'
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '更新失败，代码异常'

