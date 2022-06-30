import requests
import time
from random import random
from blockchain import Blockchain
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
            Blockchain.createHeartbeat()
            time.sleep(BLOCK_TIME)

Heartbeat().initHeartbeat()