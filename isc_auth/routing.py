#coding:utf-8

from channels import route
from channels.routing import null_consumer
from .consumers import ws_connect,ws_message,ws_disconnect,auth_message_handle,send_account_info_handle
from isc_auth.explicit_auth.consumers import explicit_auth_message_handle
from isc_auth import consumers
from isc_auth.tools.auth_tools.app_auth_tools import EXPLICIT_REPLY_COMMAND,REQUIRE_INFO_COMMAND,WIFI_REPLY_COMMAND, WIFI_DATA_COMMAND

from isc_auth.tools.auth_tools import timer

websocket_path = r"^/api-(?P<api_hostname>[a-zA-Z0-9]+)/(?P<identifer>[a-zA-Z0-9]+)/(?P<device_type>[a-zA-Z0-9]+)$"


general_routing = [
    route("websocket.connect",ws_connect,path=websocket_path),
    route("websocket.receive",ws_message,path=websocket_path),
    route("websocket.disconnect",ws_disconnect,path=websocket_path),
]

custom_routing = [
    #mobile websocket连接建立认证
    route("auth_message.receive",auth_message_handle,path=websocket_path),
    #mobile显示认证
    route("message.receive",explicit_auth_message_handle,path=websocket_path, action=EXPLICIT_REPLY_COMMAND),
    route("message.receive",send_account_info_handle,path=websocket_path, action=REQUIRE_INFO_COMMAND),

    #pc websocket连接建立认证
    route("pc_auth_message.receive", consumers.pc_auth_message_handle, path=websocket_path),
    #wifi相关
    route("message.receive", consumers.wifi_reply_handle, path=websocket_path, action=WIFI_REPLY_COMMAND),
    route("message.receive", consumers.wifi_data_handle, path=websocket_path, action=WIFI_DATA_COMMAND),

    #其余关闭
    route("message.receive", null_consumer),

    #计时器
    route("timer", timer.run),
]
