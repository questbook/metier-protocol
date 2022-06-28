import requests
import time
from random import random
import json
config = json.loads(open("./config.json", "r").read())

hostName = config["hostName"]
hostPort = str(config["hostPort"])
peers = config["peerNodes"]

BLOCK_TIME = 10
class Heartbeat:
    def initHeartbeat(self):
        print("Starting heartbeat")
        while True:
            syncParity = int(time.time()) % BLOCK_TIME
            if syncParity  == 0:
                break
            time.sleep(0.5)
            print("Waiting for sync heartbeat ...", syncParity)
        print("Sync found")
        while True:
            heartbeat = random() * 1000
            print("New block time")
            try:
                requests.post(("http://"+hostName+":"+hostPort), "operation=HEARTBEAT&heartbeat=%d"%heartbeat, timeout=2)    
            except Exception as e:
                print(e)
                pass
            finally:
                print("heartbeat sent")

            time.sleep(BLOCK_TIME)

Heartbeat().initHeartbeat()