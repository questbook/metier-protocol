from http.server import BaseHTTPRequestHandler, HTTPServer
from cgi import parse_header, parse_multipart
from urllib.parse import parse_qs
import requests
import sqlite3
import time

dbConnection = sqlite3.connect("whisper.db")
cursor = dbConnection.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS listeners(ip TEXT, retry INT)''')

hostName = "localhost"
hostPort = 9000

class WhisperServer(BaseHTTPRequestHandler):
    ALLOWED_OPERATIONS = [
        "BLOCK", # Block publication
        "STORE", 
        "QUERY", 
        "CHALLENGE", 
        "RESPOND", # respond to challenge
        "LISTEN" # Add to whisper broadcast
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
        listeners = cursor.execute("SELECT * FROM listeners WHERE ip = '%s'"% ip).fetchall()
        if not listeners and len(listeners) < 200:
            cursor.execute("INSERT INTO listeners VALUES ('%s', 0)" % ip)
            return (201, "ADDED")
        if listeners:
            return (202, "ALREADY EXISTS")
        return (405, "NOT ABLE TO ACCOMODATE")
        
    
    def operate(self, body):
        operation = body[b"operation"][0]
        if operation == b"LISTEN":
            return self.handleListen(body)
            # add to broadcast list
        elif operation == "BLOCK":
            pass
            # process block
        elif operation in self.ALLOWED_OPERATIONS:
            pass
            # add to mempool
    def forward(self, data):
        body = parse_qs(data, keep_blank_values=1)  
        if not self.isValid(data) or body[b"operation"] == "LISTEN":
            return
        hash = self.generateRequestHash(body)
        listeners = cursor.execute("SELECT * FROM listeners")
        print(listeners)
        for listener in listeners:
            print(listener)
            try:
                requests.post("http://"+listener[0]+":"+str(hostPort), data=body)
            except Exception as e:
                print(e)







    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("OK", "utf-8"))
    def do_POST(self):
        length = int(self.headers['content-length'])
        data = self.rfile.read(length)
        body = parse_qs(data, keep_blank_values=1)  
        print(body)
        self.operate(body)
        if not body[b"operation"][0] == b"LISTEN":
            self.forward(data)

myServer = HTTPServer((hostName, hostPort), WhisperServer)
print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
