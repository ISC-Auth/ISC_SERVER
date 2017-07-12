#coding:utf-8

from channels.sessions import session_for_reply_channel
from channels.asgi import get_channel_layer
from channels import Channel
import json
import random
from isc_auth.tools.auth_tools.app_auth_tools import decrypt_json_to_object

def createRandomFields(size):
    choice = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456789'
    ret = []
    for i in range(size):
        ret.append(random.choice(choice))
    return ''.join(ret)


def del_chanell_session(message,*sessions):
    for session in sessions:
        if session in message.channel_session:
            del message.channel_session[session]


def get_session_from_group(group_name, device_type, session=None):
    print(group_name)
    if len(get_channel_layer().group_channels(group_name)) > 0:
        channels_list = list(get_channel_layer().group_channels(group_name).keys())
    
        for channel in channels_list:
            print(channel)
            sessions = session_for_reply_channel(channel)
            if sessions["device_type"] == device_type:
                if session is not None:
                    sessions = sessions.get(session, None)
                return sessions

    return None

def get_session_from_channels(channels_list, device_type, session=None):
    for channel in channels_list:
        sessions = session_for_reply_channel(channel)
        if sessions["device_type"] == device_type:
            if session is not None:
                sessions = sessions.get(session, None)
            return sessions

    return None


def multiplex_auth(message,channel):
    payload = {}
    payload['reply_channel'] = message.content['reply_channel']
    payload['path'] = message.content['path']
    payload['text'] = message.content['text']
    Channel(channel).send(payload)

def multiplex(message,channel):
    try:
        content = decrypt_json_to_object(message.content['text'],message['key'])
    except:
        message.reply_channel.send({"text":"Your data format should be json"})
        message.reply_channel.send({"close":True})
        return
    
    action = content.get("action","")
    payload = {}
    payload['reply_channel'] = message.content['reply_channel']
    payload['path'] = message.content['path']
    #content为python字典
    payload['text'] = content
    payload['action'] = action
    Channel(channel).send(payload)

def pc_multiplex(message, channel):
    try:
        content = json.loads(message.content['text'])
    except:
        message.reply_channel.send({"text":"Your data format should be json"})
        message.reply_channel.send({"close":True})
        return

    action = content.get("action","")
    payload = {}
    payload['reply_channel'] = message.content['reply_channel']
    payload['path'] = message.content['path']
    #content为python字典
    payload['text'] = content
    payload['action'] = action
    Channel(channel).send(payload)

