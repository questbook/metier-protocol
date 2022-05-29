from node import NodeServer
from heartbeat import Heartbeat
from threading import Thread
from http.server import HTTPServer
import time



hostName = "localhost"
hostPort = 9000
def startNode() :    
    myServer = HTTPServer((hostName, hostPort), NodeServer)
    print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

    try:
        myServer.serve_forever()
    except KeyboardInterrupt:
        pass

    myServer.server_close()
    print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))

def startHeartbeat() :
    heartbeat = Heartbeat()
    heartbeat.initHeartbeat()

Thread(target=startNode).start()
Thread(target=startHeartbeat).start()
