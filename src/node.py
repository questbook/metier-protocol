import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
from cgi import parse_header, parse_multipart
import sys
import threading
from urllib.parse import parse_qs
import requests
import time
from explorer import Explorer
from mempool import Mempool
from blockchain import Blockchain
import pickle
import psycopg2

dbConnection = psycopg2.connect(database="metieruser", user = "metieruser", password = "metier123", host = "127.0.0.1", port = "5432")
cursor = dbConnection.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS listeners (id SERIAL PRIMARY KEY, ip TEXT, retry INT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS forwards (hash TEXT, receivedAt INT)''')
dbConnection.commit()
hostName = "localhost"
hostPort = 9000


MAX_FORWARD_RETRY = 5


mempool = Mempool()
blockchain = Blockchain(mempool)
explorer = Explorer(blockchain, mempool)


class NodeServer(BaseHTTPRequestHandler):
    ALLOWED_OPERATIONS = [
        b"BLOCK", # Block publication
        b"STORE", 
        b"QUERY", 
        b"CHALLENGE", 
        b"RESPONSE", # submitting a query response onchain
        b"RESPOND", # respond to challenge
        b"SUBMISSION", # Submit an accepted transaction on chain
        b"LISTEN", # Add to whisper broadcast
        b"LINKUSER", # link user address to datasource identifier (e.g. githb username)
        b"CONFIRM", # consensus 
    ]
    def isValid(self, data) :
        body = parse_qs(data, keep_blank_values=1)
        operation = body[b"operation"]
        # todo: check if data format is correct 
        # allowed operations : BLOCK, STORE, QUERY, CHALLENGE, RESPOND, LISTEN
        return True
    
    def generateRequestHash(self, body):
        return "todo"

    def handleListen(self, body) :
        ip = body[b"ip"][0].decode("utf-8")
        query = cursor.execute("SELECT * FROM listeners WHERE ip = '%s'"% ip)
        listeners = []
        if cursor.rowcount > 0:
           listeners= query.fetchall() 
        if not listeners and len(listeners) < 200:
            cursor.execute("INSERT INTO listeners VALUES (0,'%s', 0)" % ip)
            dbConnection.commit()
            return (201, "ADDED")
        if listeners:
            return (202, "ALREADY EXISTS")
        return (405, "NOT ABLE TO ACCOMODATE")
        
    
    def operate(self, data):
        body = parse_qs(data, keep_blank_values=1)      
        operation = body[b"operation"][0]
        if operation == b"LISTEN":
            return self.handleListen(body)
            # add to broadcast list
        if operation == b"HEARTBEAT":
            blockchain.onHeartbeat()
            return str(int(body[b"heartbeat"][0]))
        elif operation == b"BLOCK":
            blockData = pickle.loads(base64.b64decode(bytes.fromhex(body[b"data"][0].decode("utf-8"))))
            blockchain.onBlockReceived(blockData)
            return "block/"+blockData["hash"]
        elif operation == b"CONFIRM":
            confirmation = pickle.loads(base64.b64decode(bytes.fromhex(body[b"data"][0].decode("utf-8"))))
            blockchain.onValidationReceived(confirmation)
            return "confirm/"+confirmation["signature"]
            # process block
        elif operation in self.ALLOWED_OPERATIONS:
            hash = mempool.add(data)
            print("added to mempool", hash)
            return hash

    def forward(self, hash, data):
        body = parse_qs(data, keep_blank_values=1)  
        if not self.isValid(data) or body[b"operation"] == "LISTEN":
            return
        cursor.execute("SELECT * FROM listeners")
        listeners = []
        if cursor.rowcount > 0:
            listeners = cursor.fetchall()
        
        cursor.execute("SELECT * FROM forwards WHERE hash='%s'"%hash)
        if cursor.rowcount > 0:
            return
        for listener in listeners:
            try:
                print("Forwarding to ", listener)
                requests.post("http://"+listener[1]+":"+str(hostPort), data=body, timeout=3)
            except Exception as e:
                print(e)
                # if host not reachable more than 5 times kick listener 
                cursor.execute("UPDATE listeners SET retry=retry+1 WHERE id=%d", listener[0])
                self._dbConnection.commit()
                if listener[2] > 4:
                    cursor.execute("DELETE FROM listeners WHERE id=%d", listeners[0])  
                    self._dbConnection.commit()






    def processRequest(self, data):
        body = parse_qs(data, keep_blank_values=1)  
        print("Processing ...", body[b"operation"])
        sys.stdout.flush()
        hash = self.operate(data)
        if not body[b"operation"][0] == b"LISTEN":
            self.forward(hash, data)
        print("====| Completed Processing %s : %s |===="%(body[b"operation"], hash))


    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes(explorer.query(self.path), "utf-8"))
    def do_POST(self):
        length = int(self.headers['content-length'])
        data = self.rfile.read(length)
        threading.Thread(target=self.processRequest, args=(data,)).start()
        self.send_response(200)
        response = bytes("OK", "utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(response)
        return

myServer = HTTPServer((hostName, hostPort), NodeServer)
print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
