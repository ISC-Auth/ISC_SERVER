from isc_auth.tools.auth_tools import app_auth_tools
from channels import Group
from django.core.cache import cache
from channels.asgi import get_channel_layer

from dashboard.models import Device
import json
import time
from isc_auth.tools.auth_tools.timer import setTimer

START_TIME=10
SCAN_TIME = 9

def start_wifi_collect(api_hostname, identifer):
    device = Device.objects.get(identifer = identifer)
    key = device.dKey

    start_time = time.time() + START_TIME
    start_seq = 1

    content_encrypt = json.dumps({
            "type": "start_wifi_collect",
            "start_time": start_time,
            "start_seq": start_seq
        })

    cache.set("user-%s-%s_wifi_start_time" %(identifer, api_hostname), start_time, None)
    cache.set("user-%s-%s_wifi_start_seq" %(identifer, api_hostname), start_seq, None)

    cache.set("user-%s-%s_wifistate_pc" %(identifer, api_hostname), False, 0)
    cache.set("user-%s-%s_wifistate_mobile" %(identifer, api_hostname), False, 0)
    def check_state():
        state_pc = cache.get("user-%s-%s_wifistate_pc" %(identifer, api_hostname), False)
        state_mobile = cache.get("user-%s-%s_wifistate_mobile" %(identifer, api_hostname), False)
        if not (state_pc and state_mobile):
            # 有任一段未到或拒绝
            # 处理策略未定
            Group("device-%s-%s" %(identifer, api_hostname)).send({"text": ""})
            print("Wifi collect starting failed.")
        else:
            cache.set("user-%s-%s_wifi_current_seq" %(identifer, api_hostname), start_seq + 1, None)

            check_time = start_time + SCAN_TIME * 2
            def wifi_data_check_closure():
                wifi_data_check(api_hostname, identifer)

            setTimer(check_time, wifi_data_check_closure)

    setTimer(start_time + SCAN_TIME, check_state)
    Group("device-%s-%s" %(identifer, api_hostname)).send({"text": content_encrypt})


def wifi_data_check(api_hostname,identifer):
    state_pc = cache.get("user-%s-%s_wifistate_pc" %(identifer, api_hostname), None)
    state_mobile = cache.get("user-%s-%s_wifistate_mobile" %(identifer, api_hostname), None)
    if state_pc == True and state_mobile == True :
        data_pc_queue = cache.get("user-%s-%s_wifidata_pc" %(identifer, api_hostname), None)
        data_mb_queue = cache.get("user-%s-%s_wifidata_mobile" %(identifer, api_hostname), None)
        if data_pc_queue and data_mb_queue:
            data_pc = data_pc_queue.popleft()
            data_mb = data_mb_queue.popleft()

            print("(mb,"+identifer+","+str(data_mb["seq"])+")")
            print("(PC,"+identifer+","+str(data_pc["seq"])+")")

            current_seq = cache.get("user-%s-%s_wifi_current_seq" %(identifer, api_hostname), 0)
            start_seq = cache.get("user-%s-%s_wifi_start_seq" %(identifer, api_hostname), 0)
            start_time = cache.get("user-%s-%s_wifi_start_time" %(identifer, api_hostname), None)
            if data_pc['seq'] == data_mb['seq'] and current_seq == data_pc['seq']:
                cache.set("user-%s-%s_wifi_current_seq" %(identifer, api_hostname), current_seq + 1, None)
                check_time = (current_seq - start_seq + 2) * SCAN_TIME + start_time

                filename = cache.get("device-%s-%s_current_output" %(identifer,api_hostname), None)
                file = open(filename, "a")
                for i in range(0, 3):
                    content = json.dumps({
                        "pc": data_pc["data"][i],
                        "mobile": data_mb["data"][i]
                    })
                    file.write(content + "\n")

                file.close()

                def wifi_data_check_closure():
                    wifi_data_check(api_hostname, identifer)

                setTimer(check_time, wifi_data_check_closure)

                cache.set("user-%s-%s_wifidata_pc" %(identifer, api_hostname), data_pc_queue, None)
                cache.set("user-%s-%s_wifidata_mobile" %(identifer, api_hostname), data_mb_queue, None)
                return  True

    cache.set("user-%s-%s_wifistate_mobile" %(identifer, api_hostname), False, 0)
    cache.set("user-%s-%s_wifistate_pc" %(identifer, api_hostname), False, 0)
    time.sleep(2)
    return False
