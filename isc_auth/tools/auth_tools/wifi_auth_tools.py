from isc_auth.tools.auth_tools import app_auth_tools
from channels import Group
from django.core.cache import cache
from channels.asgi import get_channel_layer

from isc_auth.models import Device
import json

import time
from isc_auth.tools.auth_tools.timer import setTimer

START_TIME=10;
SCAN_STEP = 20;
SCAN_TIME = 9;

def start_wifi_collect(api_hostname, identifer):
	device = Device.objects.get(identifer = identifer)
	key = device.dKey

	start_time = time.time() + START_TIME
	start_seq = 1
	time_step = SCAN_STEP

	content_encrypt = json.dumps({
			"type": "start_wifi_collect",
			"start_time": start_time,
			"start_seq": start_seq
		})

	cache.set("user-%s-%s_wifi_start_time" %(identifer, api_hostname), start_time)
	cache.set("user-%s-%s_wifi_start_seq" %(identifer, api_hostname), start_seq)

	cache.set("user-%s-%s_wifistate_pc" %(identifer, api_hostname), False)
	cache.set("user-%s-%s_wifistate_state" %(identifer, api_hostname), False)
	def check_state():
		state_pc = cache.get("user-%s-%s_wifistate_pc" %(identifer, api_hostname), False)
        state_mobile = cache.get("user-%s-%s_wifistate_mobile" %(identifer, api_hostname), False)

		if not (state_pc and state_mobile):
			# 有任一段未到或拒绝
			# 处理策略未定
			print("Wifi collect starting failed.")

	setTimer(start_time + SCAN_TIME, check_state)

	print(get_channel_layer().group_channels("device-%s-%s" %(identifer, api_hostname)).__len__())
	Group("device-%s-%s" %(identifer, api_hostname)).send({"text": content_encrypt})
