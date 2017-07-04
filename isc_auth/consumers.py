#coding:utf-8
from channels import Group,Channel
from channels.sessions import channel_session
from django.core.cache import cache

import json,time
from queue import Queue
from isc_auth.tools.auth_tools import app_auth_tools, duoTools
from isc_auth.tools.uniform_tools import *
from .models import Device
from django.db.models import Empty
from isc_auth.tools.auth_tools.timer import setTimer

WIFI_REPLY_NOSTATE = 0b0
WIFI_REPLY_MOBILE_ACCEPT = 0b1
WIFI_REPLY_PC_ACCEPT = 0b10

globalVar = globals()

@channel_session
def ws_connect(message,api_hostname,identifer, device_type):
    message.reply_channel.send({'accept':True})

    if device_type == 'mobile':
        #检查cache和数据库
        try:
            key = cache.get("device-%s-%s_key" %(identifer,api_hostname),None) or Device.objects.get(identifer=identifer)
        except Device.DoesNotExist:
            #未开始绑定，且不存在该设备
            message.reply_channel.send({"close":True})
            return
        else:
            #若未开始绑定
            if isinstance(key,Device):
                #若设备未激活,关闭连接
                if not key.is_activated:
                    message.reply_channel.send({"close":True})
                    return
                else:
                    key = key.dKey

        random_number,code = app_auth_tools.gen_b64_random_and_code(key,app_auth_tools.CONNECTION_SETUP_PREFIX)

        message.channel_session["key"] = key
        message.channel_session["auth"] = False
        message.channel_session["setup_random"] = random_number

        message.reply_channel.send({'text':code})

    elif device_type == 'pc':
        key = cache.get("device-%s-%s_pc_key" %(identifer,api_hostname), None)
        if key:
            # 该用户被授权启用PC客户端
            random_number = createRandomFields(20)

            code = json.dumps({
                "type": app_auth_tools.CONNECTION_SETUP_PREFIX,  #SYN
                "random": random_number
            })

            message.channel_session["key"] = key
            message.channel_session["auth"] = False
            message.channel_session["setup_random"] = random_number

            message.reply_channel.send({'text':code})

        else:
            message.reply_channel.send({"close":True})

    else:
        message.reply_channel.send({"close":True})



@channel_session
def ws_message(message,api_hostname,identifer, device_type):
    if device_type == 'mobile':
        #若已经过认证（已建立合法通道）
        if message.channel_session['auth']:
            message['key'] = message.channel_session['key']
            multiplex(message,"message.receive")
        else:
            multiplex_auth(message,"auth_message.receive")
    elif device_type == 'pc':
        if message.channel_session['auth']:
            pc_multiplex(message, "message.receive")
        else:
            multiplex_auth(message, "pc_auth_message.receive")





@channel_session
def ws_disconnect(message,api_hostname,identifer, device_type):
    Group("device-%s-%s" %(identifer,api_hostname)).discard(message.reply_channel)


def not_find_action(message,api_hostname,identifer):
    pass


def send_account_info_handle(message,api_hostname,identifer):
    device = Device.objects.get(identifer=identifer)
    key = device.dKey
    seed = device.seed
    content_encrypt = app_auth_tools.base64_encrypt(key,json.dumps({
                "type":"info",
                "data":"test data",
                "seed":seed
            }))
    message.reply_channel.send({
        "text":content_encrypt
    })

@channel_session
def illegal_connection_handle(message):
    message.reply_channel.send({"close":True})

@channel_session
def auth_message_handle(message,api_hostname,identifer):
    '''
    用于检测APP回传的加密信息，建立合法通道
    '''
    #test
    # message.channel_session['auth'] = True
    # Group("device-%s-%s" %(identifer,api_hostname)).add(message.reply_channel)
    # message.reply_channel.send({"text":app_auth_tools.base64_encrypt(message.channel_session["key"],"OK")})
    key = message.channel_session['key']
    info = message.content["text"]
    random = message.channel_session['setup_random']
    try:
        prefix, = app_auth_tools.decrypt_and_validate_info(info,key,random,app_auth_tools.CONNECTION_REPLY_PREFIX)
    except Exception as e:
        message.reply_channel.send({"close":True})
        return
    else:
        #认证通过,置session位，并将其加入Group
        message.channel_session['auth'] = True
        message.reply_channel.send({"text":app_auth_tools.base64_encrypt(message.channel_session["key"],"OK")})
        Group("device-%s-%s" %(identifer,api_hostname)).add(message.reply_channel)

@channel_session
def pc_auth_message_handle(message, api_hostname, identifer, device_type):
    key = message.channel_session['key']
    random = message.channel_session['setup_random']
    random_trans = duoTools._hmac_sha1(key, random)

    jsondata = json.loads(message.content['text'])

    if jsondata['random'] == random_trans:
        message.channel_session['auth'] = True
        message.reply_channel.send({"text": "OK"})
        Group("device-%s-%s" %(identifer,api_hostname)).add(message.reply_channel)
    else:
        message.reply_channel.send({"close":True})


@channel_session
def wifi_reply_handle(message, api_hostname, identifer, device_type):
    source = message.content["text"]["source"]
    result = message.content["text"]["result"]
    seq = message.content["text"]["seq"]

    start_seq = cache.get("user-%s-%s_wifi_start_seq" %(identifer, api_hostname), 0)

    print("+++ source ++++"+source+"++++ seq ++  "+str(seq)+"  +++ start seq ++ "+str(start_seq))
    if start_seq == seq:

        state_pc = cache.get("user-%s-%s_wifistate_pc" %(identifer, api_hostname), False)
        state_mobile = cache.get("user-%s-%s_wifistate_mobile" %(identifer, api_hostname), False)

        if result == "deny" or source == "mobile" and state_mobile == True   or source == "pc" and state_pc == True:
            #任一端拒绝或者单端重复发包，重置状态并返回暂停包
            Group("device-%s-%s" %(identifer, api_hostname)).send({"text": ""})

            state = WIFI_REPLY_NOSTATE
            cache.set("user-%s-%s_wifistate_pc" %(identifer, api_hostname), False)
            cache.set("user-%s-%s_wifistate_mobile" %(identifer, api_hostname), False)
        else:
            if source == "mobile":
                cache.set("user-%s-%s_wifistate_mobile" %(identifer, api_hostname), True)
            elif source == "pc":
                cache.set("user-%s-%s_wifistate_pc" %(identifer, api_hostname), True)

@channel_session
def wifi_data_handle(message, api_hostname, identifer, device_type):
    # 数据包处理 创建两个队列 PC端和mobile端
    print(time.asctime( time.localtime(time.time())))
    #print("wifi_data_handle not implemented")

    data = message.content["text"]
    source = data["source"]
    seq = data["seq"]

    state_pc = cache.get("user-%s-%s_wifistate_pc" %(identifer, api_hostname), None)
    state_mobile = cache.get("user-%s-%s_wifistate_mobile" %(identifer, api_hostname), None)

    if state_pc == True and state_mobile == True :
        if source == "mobile":
            if 'wifi_data_mb_'+identifer in globals().keys():
                print("-------mobile--------")
            else:
                globalVar['wifi_data_mb_'+identifer] = Queue()

            globalVar['wifi_data_mb_'+identifer].put(data)
            print("--mb----"+identifer+"----------"+str(data["seq"])+"---")

        elif source == "pc":
            if 'wifi_data_pc_'+identifer in globals().keys():
                print("---------pc---------")
            else:
                globalVar['wifi_data_pc_'+identifer] = Queue()

            globalVar['wifi_data_pc_'+identifer].put(data)
            print("--pc----"+identifer+"----------"+str(data["seq"])+"---")

def wifi_data_check(api_hostname,identifer):
    state_pc = cache.get("user-%s-%s_wifistate_pc" %(identifer, api_hostname), None)
    state_mobile = cache.get("user-%s-%s_wifistate_mobile" %(identifer, api_hostname), None)
    if state_pc == True and state_mobile == True :
        if 'wifi_data_mb_'+identifer in globals().keys() and 'wifi_data_pc_'+identifer in globals().keys():
            if not(globalVar['wifi_data_mb_'+identifer].empty() or globalVar['wifi_data_pc_'+identifer].empty()):
                data_pc = globalVar['wifi_data_pc_'+identifer].get()
                data_mb = globalVar['wifi_data_mb_'+identifer].get()

                print("(mb,"+identifer+","+str(data_mb["seq"])+")")
                print("(PC,"+identifer+","+str(data_pc["seq"])+")")

                current_seq = cache.get("user-%s-%s_wifi_current_seq" %(identifer, api_hostname), 0)
                start_seq = cache.get("user-%s-%s_wifi_start_seq" %(identifer, api_hostname), 0)
                start_time = cache.get("user-%s-%s_wifi_start_time" %(identifer, api_hostname), None)
                if data_pc['seq'] == data_mb['seq'] and current_seq == data_pc['seq']:
                    cache.set("user-%s-%s_wifi_current_seq" %(identifer, api_hostname), current_seq + 1)
                    SCAN_TIME = cache.get("user-%s-%s_wifi_scan_time" %(identifer, api_hostname), None)
                    check_time = (current_seq - start_seq + 1) * SCAN_TIME + start_time

                    def wifi_data_check_closure():
                        wifi_data_check(api_hostname, identifer)

                    setTimer(check_time, wifi_data_check_closure)
                    return  True

    cache.set("user-%s-%s_wifistate_mobile" %(identifer, api_hostname), False)
    cache.set("user-%s-%s_wifistate_pc" %(identifer, api_hostname), False)
    time.sleep(2)
    return False
