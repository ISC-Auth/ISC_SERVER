from isc_auth.tools import app_auth_tools
from channels import Group
from django.core.cache import cache

from .models import Device
import json
from isc_auth.consumers import WIFI_REPLY_NOSTATE

def start_wifi_collect(api_hostname, identifer):
	device = Device.objects.get(identifier = identifer)
	key = device.dKey

	content_encrypt = app_auth_tools.base64_encrypt(key, json.dumps({
			"type": "start_wifi_collect",
			"start_time": "",
			"start_seq": "",
			"time_step": ""
		}))

	cache.set("user-%s-%s_wifistate" %(identifer, api_hostname), WIFI_REPLY_NOSTATE)

	Group("device-%s-%s" %(identifer, api_hostname)).send({"text": content_encrypt})