import requests
import time

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
            t = int(time.time())
            heartbeat = int(t/10)*10
            print("New block time")
            try:
                print("sending heart beat")
                requests.post("http://localhost:9000/", "operation=HEARTBEAT&heartbeat=%d"%heartbeat, timeout=2)    
            except Exception as e:
                print(e)
                pass
            finally:
                print("heartbeat sent")

            time.sleep(BLOCK_TIME)

Heartbeat().initHeartbeat()