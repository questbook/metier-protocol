import sqlite3
from time import time
from urllib.parse import parse_qs

class Mempool :
    _dbConnection = None
    _cursor = None

    def __init__(self):
        self._dbConnection = sqlite3.connect("mempool.db")
        self._cursor = self._dbConnection.cursor()
        self._cursor.execute("CREATE TABLE IF NOT EXISTS mempool (opHash TEXT, opRaw TEXT, opTimestamp INT)")
    
    def isValid(self, data):
        # todo: verify signature
        # todo: verify validity
        return True
    def hash(self, body):
        return "todo"+str(int(time.time()))
    def add(self, data):
        raw = data.decode("utf-8")
        body = parse_qs(data, keep_blank_values=1)  
        hash = self.hash(body)
        self._cursor.execute("INSERT INTO mempool VALUES('%s', '%s', %d"%(hash, raw, int(time.time())))
        print("Added %s to mempool"%hash)
        return hash

