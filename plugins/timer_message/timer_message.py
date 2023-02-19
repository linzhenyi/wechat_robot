from plugin_interface import PluginInterface
import threading
import time
import traceback
import json
import datetime
import os
from dateutil.relativedelta import relativedelta

NAME = '定时提醒'
ADD = '增加'
DEL = '删除'
QRY = '查询'
TIMER_OBJ = '对象'
TIMER_CONTENT = '内容'
TIMER_NOTIFY_NICKNAME = '提醒人'
TIMER_NEXT_PUSH_TIME = '下次提醒时间'
TIMER_REPEAT_ELAPSE = '重复周期'
TIMER_REPEAT_UNIT = '重复单位'
TIMER_OWNER = '设置人'

DATA_FILE = os.path.dirname(os.path.realpath(__file__)) + '/push_list.json'
DATE_FILE_JSON_ROOT = 'push_list'


class PluginImp(PluginInterface):
    def __init__(self):
        super().__init__()
        self.timer_data_lock = threading.RLock()
        self.thread_timer = threading.Thread(target=self.__thread_timer)
        self.thread_timer_stop = False
        self.timer_data = None
        self.need_load_file_data = True

    def get_name(self):
        return '定时提醒'

    def get_help(self):
        return '一次性或定时向私人\\群发送消息。具体参数有：\n' + ADD + '\n' + DEL + '\n' + QRY + '\n' + \
               '具体格式如：\n' + ADD + ' 用户或群ID+提醒内容+提醒人+第一次提醒时间+重复周期+重复单位\n' \
               + DEL + ' 前先查询，将需要删除的整条记录复制作为参数\n' + QRY + ' 无需参数\n' \
               '用户或群ID通过获取调试信息得到；提醒人主要用来在群里@，可为空；重复单位目前支持月/周/天/工作日/小时，无需重复可为空' \
               '例如：\n' + ADD + ' wxid_abc+3楼会议室开会++2022-03-11-15:00:00+1+周'

    def module_load(self):
        super().module_load()
        self.thread_timer.start()

    def module_unload(self):
        super().module_unload()
        self.thread_timer_stop = True
        self.thread_timer.join(timeout=10)
        if self.thread_timer.is_alive():
            print('timer message thread quit time out')

    def handle_recv_msg(self, msg, wxid=None, roomid=None, nickname=None):
        super().handle_recv_msg(msg, wxid, roomid, nickname)
        if not super().is_greater_than_user(wxid):
            super().send_msg('权限不足，请联系管理员添加权限', wxid, roomid, nickname)
            return
        ret_data = self.__handle_cmd(msg, wxid)
        super().send_msg(ret_data, wxid, roomid, nickname)

    def __handle_cmd(self, msg, wxid):
        find_index = msg.find(' ')
        if find_index != -1:
            cmd = msg[0: find_index]
            msg = msg[find_index + 1:]
        else:
            cmd = msg
        cmd_list = msg.split('+')
        try:
            self.timer_data_lock.acquire()
            ret_msg = self.__exec_cmd(cmd, cmd_list, msg, wxid)
            self.timer_data_lock.release()
            return ret_msg
        except Exception:
            self.timer_data_lock.release()
            raise

    def __exec_cmd(self, cmd, cmd_list, msg, wxid):
        push_list_dict = self.__load_push_list()
        if cmd == DEL:
            for item in push_list_dict[DATE_FILE_JSON_ROOT]:
                if str(item) == msg:
                    push_list_dict[DATE_FILE_JSON_ROOT].remove(item)
                    self.__save_push_list(push_list_dict)
                    return '删除成功'
            return '未找到删除对象'
        if cmd == ADD:
            next_push_time = datetime.datetime.strptime(cmd_list[3], '%Y-%m-%d-%H:%M:%S')
            if datetime.datetime.now() > next_push_time:
                return '设定时间不能小于当前时间'
            new_item = {TIMER_OBJ: cmd_list[0], TIMER_CONTENT: cmd_list[1], TIMER_NOTIFY_NICKNAME: cmd_list[2],
                        TIMER_NEXT_PUSH_TIME: cmd_list[3], TIMER_REPEAT_ELAPSE: cmd_list[4],
                        TIMER_REPEAT_UNIT: cmd_list[5], TIMER_OWNER: wxid}
            push_list_dict[DATE_FILE_JSON_ROOT].append(new_item)
            self.__save_push_list(push_list_dict)
            return '增加成功'
        if cmd == QRY:
            if super().is_greater_than_super_admin(wxid):
                return str(push_list_dict[DATE_FILE_JSON_ROOT])
            else:
                for item in push_list_dict[DATE_FILE_JSON_ROOT]:
                    ret_list = []
                    if item[TIMER_OWNER] == wxid:
                        ret_list.append(item)
                    return str(ret_list)
        return '指令有误'

    def __load_push_list(self):
        if not os.path.exists(DATA_FILE):
            return {DATE_FILE_JSON_ROOT: []}
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            push_list_dict = json.load(f)
        return push_list_dict

    def __save_push_list(self, push_list_dict):
        json_str = json.dumps(push_list_dict)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            f.write(json_str)
        self.need_load_file_data = True

    def __thread_timer(self):
        push_list_dict = {DATE_FILE_JSON_ROOT: []}
        while True:
            try:
                time.sleep(1)
                if self.thread_timer_stop:
                    break
                if self.need_load_file_data:
                    push_list_dict = self.__load_push_list()
                    self.need_load_file_data = False
                try:
                    self.timer_data_lock.acquire()
                    new_push_list_dict, push_list = self.__thread_timer_get_push_data(push_list_dict)
                    if push_list:   # 有通知的内容才会改变，有改变才需要保存
                        self.__save_push_list(new_push_list_dict)
                    self.timer_data_lock.release()
                except Exception:
                    self.timer_data_lock.release()
                    raise
                for item in push_list:
                    roomid = None
                    wxid = None
                    nickname = None
                    if item[TIMER_OBJ].find('@chatroom') == -1:
                        wxid = item[TIMER_OBJ]
                    else:
                        roomid = item[TIMER_OBJ]
                    if item[TIMER_NOTIFY_NICKNAME]:
                        nickname = item[TIMER_NOTIFY_NICKNAME]
                    super().send_msg(item[TIMER_CONTENT], wxid, roomid, nickname)

            except Exception as e:
                print(e)
                traceback.print_exc()

    def __thread_timer_get_push_data(self, push_list_dict):
        new_push_list_dict = {DATE_FILE_JSON_ROOT: []}
        push_list = []
        for item in push_list_dict[DATE_FILE_JSON_ROOT]:
            next_push_time = datetime.datetime.strptime(item[TIMER_NEXT_PUSH_TIME], '%Y-%m-%d-%H:%M:%S')
            delete = False
            if datetime.datetime.now() > next_push_time:
                repeat_elapse = 0
                if item[TIMER_REPEAT_ELAPSE]:
                    repeat_elapse = int(item[TIMER_REPEAT_ELAPSE])
                if item[TIMER_REPEAT_UNIT] == '月':
                    next_push_time += relativedelta(months=+repeat_elapse)
                elif item[TIMER_REPEAT_UNIT] == '周':
                    next_push_time += relativedelta(weeks=+repeat_elapse)
                elif item[TIMER_REPEAT_UNIT] == '天':
                    next_push_time += relativedelta(days=+repeat_elapse)
                elif item[TIMER_REPEAT_UNIT] == '工作日':
                    next_push_time += relativedelta(days=+repeat_elapse)
                    if next_push_time.weekday() == 5:  # Saturday
                        next_push_time += relativedelta(days=+2)
                    if next_push_time.weekday() == 6:  # Sunday
                        next_push_time += relativedelta(days=+1)
                elif item[TIMER_REPEAT_UNIT] == '小时':
                    next_push_time += relativedelta(hours=+repeat_elapse)
                else:   # 不需要重复
                    delete = True
                item[TIMER_NEXT_PUSH_TIME] = next_push_time.strftime('%Y-%m-%d-%H:%M:%S')
                push_list.append(item)
            if not delete:
                new_push_list_dict[DATE_FILE_JSON_ROOT].append(item)
        return new_push_list_dict, push_list
