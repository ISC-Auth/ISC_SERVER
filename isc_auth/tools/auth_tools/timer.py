import time
from channels import Channel

def setTimer(deadline, func):
	payload = {
		"path": "/",
		"deadline": deadline,
		"func": func
	}

	Channel("timer").send(payload)


def run(message):
	sleepTime = message.content["deadline"] - time.time()
	time.sleep(sleepTime)

	func = message.content["func"]

	func()