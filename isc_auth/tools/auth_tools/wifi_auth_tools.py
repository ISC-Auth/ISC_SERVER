from isc_auth.tools.auth_tools import app_auth_tools
from channels import Group
from django.core.cache import cache
from channels.asgi import get_channel_layer

from isc_auth.models import Device
import json
import time
from isc_auth.tools.auth_tools.timer import setTimer
from isc_auth.consumers import wifi_data_check

START_TIME=10
SCAN_STEP = 5
SCAN_TIME = 9
globalVar = globals()
global check_time

def start_wifi_collect(api_hostname, identifer):
	device = Device.objects.get(identifer = identifer)
	key = device.dKey

	start_time = time.time() + START_TIME
	start_seq = 1
	print(time.asctime( time.localtime(time.time())))

	content_encrypt = json.dumps({
			"type": "start_wifi_collect",
			"start_time": start_time,
			"start_seq": start_seq
		})

	cache.set("user-%s-%s_wifi_start_time" %(identifer, api_hostname), start_time)
	cache.set("user-%s-%s_wifi_start_seq" %(identifer, api_hostname), start_seq)

	cache.set("user-%s-%s_wifistate_pc" %(identifer, api_hostname), False)
	cache.set("user-%s-%s_wifistate_mobile" %(identifer, api_hostname), False)
	def check_state():
		wifi_data_check(api_hostname,identifer)
		state_pc = cache.get("user-%s-%s_wifistate_pc" %(identifer, api_hostname), False)
		state_mobile = cache.get("user-%s-%s_wifistate_mobile" %(identifer, api_hostname), False)
		if not (state_pc and state_mobile):
			# 有任一段未到或拒绝
			# 处理策略未定
			Group("device-%s-%s" %(identifer, api_hostname)).send({"text": ""})
			print("Wifi collect starting failed.")
		else:
			global check_time
			print(str(time.ctime(check_time))+'===== now ======')
			check_time += SCAN_TIME
			print(str(time.ctime(check_time))+'===== next ======')
			setTimer(check_time, check_state)

	global check_time
	check_time = start_time + SCAN_TIME+ SCAN_STEP
	print(str(time.ctime(check_time))+'   check_time_1')
	setTimer(check_time, check_state)
	Group("device-%s-%s" %(identifer, api_hostname)).send({"text": content_encrypt})
