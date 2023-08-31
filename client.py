# coding=utf-8

import websocket
import time
import json
import requests
import threading
import xml.etree.ElementTree as ET
from plugins_mgr import PluginsMgr
from plugin_interface import *
from context import Context

websocket._logging._logger.level = -99

ip = '127.0.0.1'
port = 5555
SERVER = f'ws://{ip}:{port}'

RECV_TXT_MSG = 1
RECV_PIC_MSG = 3
RECV_TXT_CITE_MSG = 49
PIC_MSG = 500
AT_MSG = 550
TXT_MSG = 555
USER_LIST = 5000
GET_USER_LIST_SUCCSESS = 5001
GET_USER_LIST_FAIL = 5002
HEART_BEAT = 5005
CHATROOM_MEMBER = 5010
CHATROOM_MEMBER_NICK = 5020
DEBUG_SWITCH = 6000
PERSONAL_INFO = 6500
PERSONAL_DETAIL = 6550
# DESTROY_ALL = 9999
JOIN_ROOM = 10000

g_id_postfix = 0
g_last_time = ''
g_plugins_mgr = PluginsMgr()
g_lock = threading.RLock()
g_max_id_queue_len = 100
g_id_queue = [None for i in range(g_max_id_queue_len)]
g_current_queue_index = 0


def push_record(msg=None, wxid=None, roomid=None, nickname=None):
    global g_id_postfix, g_last_time, g_max_id_queue_len, g_current_queue_index
    time_now = time.strftime("%Y%m%d%H%M%S")
    if not g_last_time == time_now:
        g_id_postfix = 0
    g_last_time = time_now
    id_postfix_format = ('00' + str(g_id_postfix))[-3:]  # 尾部数字范围000-999
    g_id_postfix = (g_id_postfix + 1) % 1000  # 每秒钟最多生成1000个不同的id
    id = time_now + id_postfix_format
    g_id_queue[g_current_queue_index] = {'id': id, 'msg': msg, 'wxid': wxid, 'roomid': roomid, 'nickname': nickname}
    g_current_queue_index = (g_current_queue_index + 1) % g_max_id_queue_len
    return id


def output(msg):
    now = time.strftime("%Y-%m-%d %X")
    print(f'[{now}]:{msg}')


def send(uri, data):
    base_data = {
        'id': push_record(),
        'type': 'null',
        'roomid': 'null',
        'wxid': 'null',
        'content': 'null',
        'nickname': 'null',
        'ext': 'null',
    }
    base_data.update(data)
    url = f'http://{ip}:{port}/{uri}'
    res = requests.post(url, json={'para': base_data}, timeout=5)
    return res.json()


def get_chatroom_member_list(msg, wxid=None, roomid=None, nickname=None):
    qs = {
        'id': push_record(msg, wxid, roomid, nickname),
        'type': CHATROOM_MEMBER,
    }
    ws_send(json.dumps(qs))


def pack_msg(msg, wxid=None, roomid=None, nickname=None):
    msg_type = AT_MSG if roomid else TXT_MSG
    qs = {  # query string
        'id': push_record(msg, wxid, roomid, nickname),
        'type': msg_type,
        'content': msg,
        'roomid': '',
        'wxid': '',
        'nickname': '',
        'ext': ''  # 必须要，不然会报错
    }
    if wxid:
        qs['wxid'] = wxid
    if roomid:
        qs['roomid'] = roomid
    if nickname:
        qs['nickname'] = nickname
    output(f'发送消息: {qs}')
    return json.dumps(qs)


def send_msg(msg, wxid=None, roomid=None, nickname=None):
    ws_send(pack_msg(msg, wxid, roomid, nickname))


def send_cmd(cmd, arg=None, owner_wxid=None, owner_roomid=None, owner_nickname=None):
    if cmd == cmd_dump:
        get_chatroom_member_list(cmd, owner_wxid, owner_roomid, owner_nickname)
    elif cmd == cmd_help:
        if not arg:
            msg = '请输入\"帮助 参数\"进行查询，可用如下参数：\n' + g_plugins_mgr.get_plugins_name()
        else:
            msg = g_plugins_mgr.get_help_txt(arg)
        send_msg(msg, owner_wxid, owner_roomid, owner_nickname)
    elif cmd == cmd_update_plugins:
        ret_msg = g_plugins_mgr.update_plugins(arg)
        send_msg(ret_msg, owner_wxid, owner_roomid, owner_nickname)
    elif cmd == cmd_update_authority:
        Context.instance().update_authority()


def ws_send(data):
    try:
        g_lock.acquire()
        websocket_server.send(data)
        g_lock.release()
    except Exception:
        g_lock.release()
        raise


def handle_nick(msg_json):
    pass


def handle_recv_msg(msg_json):
    global g_plugins_mgr
    output(f'收到消息:{msg_json}')
    content = msg_json['content']
    at_name = ''
    if content and content[0] == '@':
        find_index = content.find('\u2005')  # \u2005是Unicode编码的空格
        at_name = content[2: find_index]
        msg = content[find_index + 1:].strip()
    else:
        msg = content.strip()
    if not 'wxid' in msg_json:  # msg send success notify or others
        return
    elif '@chatroom' in msg_json['wxid']:
        roomid = msg_json['wxid']
        senderid = msg_json['id1']
    else:
        roomid = None
        senderid = msg_json['wxid']

    if roomid:
        xml_root = ET.fromstring(msg_json['id3'])
        at_user_list = ''
        for child in xml_root:
            if child.tag == 'atuserlist':
                at_user_list = child.text
                at_user_list = at_user_list.strip(',') #pc端微信@时前面会多一个,
                break
        if not at_user_list:
            return
        self_wx_id = Context.instance().get_authority_cfg()['self']
        at_me_msg = at_user_list == self_wx_id and at_name != 'all people' and at_name != '所有人'\
            and at_name != 'notify@all' and at_name != 'notify@所有人' #@all被微信当作@个人处理，无法从其他地方判断
        if not at_me_msg:
            return
    nickname = get_member_nick(roomid, senderid)
    g_plugins_mgr.handle_recv_msg(msg, senderid, roomid, nickname)


def get_member_nick(roomid, wxid):
    # 获取指定群的成员的昵称 或 微信好友的昵称
    uri = 'api/getmembernick'
    data = {
        'type': CHATROOM_MEMBER_NICK,
        'wxid': wxid,
        'roomid': roomid or 'null'
    }
    resp_json = send(uri, data)
    return json.loads(resp_json['content'])['nick']


def hanle_member_list(msg_json):
    # address member room_id
    msg_id = msg_json['id']
    content = msg_json['content']
    msg_record = None
    for msg_item in g_id_queue:
        if msg_item and msg_item['id'] == msg_id:
            msg_record = msg_item
            break
    room_id = msg_record['roomid']
    member = []
    for group_item in content:
        if group_item['room_id'] == room_id:
            member = group_item['member']
            break
    member_info = []
    for member_wx_id in member:
        nickname = get_member_nick(room_id, member_wx_id)
        member_info.append((member_wx_id, nickname))
    if member_info:
        ret_msg = msg_record['roomid'] + ':' + str(member_info)
        send_msg(ret_msg, msg_record['wxid'])


def handle_msg_cite(msg_json):
    pass


def heartbeat(msg_json):
    # output(msg_json['content'])
    pass


def send_wxuser_list():
    qs = {
        'id': push_record(),
        'type': USER_LIST,
        'content': 'user list',
        'wxid': 'null',
    }
    ws_send(json.dumps(qs))


def handle_wxuser_list(msg_json):
    Context.instance().set_user_list(msg_json['content'])


def welcome_join(msg_json):
    pass


def on_message(ws, message):
    print(ws)
    j = json.loads(message)
    resp_type = j['type']
    # switch结构
    action = {
        CHATROOM_MEMBER_NICK: handle_nick,
        PERSONAL_DETAIL: handle_recv_msg,
        AT_MSG: handle_recv_msg,
        DEBUG_SWITCH: handle_recv_msg,
        PERSONAL_INFO: handle_recv_msg,
        TXT_MSG: handle_recv_msg,
        PIC_MSG: handle_recv_msg,
        CHATROOM_MEMBER: hanle_member_list,
        RECV_PIC_MSG: handle_recv_msg,
        RECV_TXT_MSG: handle_recv_msg,
        RECV_TXT_CITE_MSG: handle_msg_cite,
        HEART_BEAT: heartbeat,
        USER_LIST: handle_wxuser_list,
        GET_USER_LIST_SUCCSESS: handle_wxuser_list,
        GET_USER_LIST_FAIL: handle_wxuser_list,
        JOIN_ROOM: welcome_join,
    }
    action.get(resp_type, print)(j)


def on_open(ws):
    global g_plugins_mgr
    print(ws)
    print('opened')
    send_wxuser_list()
    g_plugins_mgr.init(send_msg, send_cmd)


def on_error(ws, error):
    print(ws)
    print('error occurred: ', error)


def on_close(ws):
    print(ws)
    print('closed')


websocket_server = websocket.WebSocketApp(SERVER,
                                          on_open=on_open,
                                          on_message=on_message,
                                          on_error=on_error,
                                          on_close=on_close)
websocket_server.run_forever()
