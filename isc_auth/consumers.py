#coding:utf-8
from channels import Group,Channel
from channels.sessions import channel_session
from django.core.cache import cache

import json
from isc_auth.tools.auth_tools import app_auth_tools, duoTools
from isc_auth.tools.uniform_tools import *
from .models import Device
from django.db.models import Empty

WIFI_REPLY_NOSTATE = 0b0
WIFI_REPLY_MOBILE_ACCEPT = 0b1
WIFI_REPLY_PC_ACCEPT = 0b10


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
def wifi_reply_handle(message, api_hostname, identifer):
    source = message.content["text"]["source"]
    result = message.content["text"]["result"]
    seq = message.content["text"]["seq"]

    start_seq = cache.get("user-%s-%s_wifistate" %(identifer, api_hostname), 0)
    if start_seq == seq:

        state = cache.get("user-%s-%s_wifistate" %(identifer, api_hostname), WIFI_REPLY_NOSTATE)

        if result == "deny" or source == "mobile" and state == WIFI_REPLY_MOBILE_ACCEPT or source == "pc" and state == WIFI_REPLY_PC_ACCEPT:
            #任一端拒绝或者单端重复发包，重置状态并返回暂停包
            Group("device-%s-%s" %(identifer, api_hostname)).send({"text": ""})

            state = WIFI_REPLY_NOSTATE
            cache.set("user-%s-%s_wifistate" %(identifer, api_hostname), state, 1)
        else:
            if source == "mobile":
                state = state | WIFI_REPLY_MOBILE_ACCEPT
            elif source == "pc":
                state = state | WIFI_REPLY_PC_ACCEPT

            cache.set("user-%s-%s_wifistate" %(identifer, api_hostname), state)

@channel_session
def wifi_data_handle(message, api_hostname, identifer):
    # 数据包处理
    print("wifi_data_handle not implemented")


@channel_session
def illegal_connection_handle(message):
    message.reply_channel.send({"close":True})
