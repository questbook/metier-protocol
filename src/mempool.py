from cgitb import text
import sqlite3
from time import time
from urllib.parse import parse_qs
from web3 import Web3
from utils import getAddressFromSignature
import utxos

class Mempool :
    _dbConnection = None
    _cursor = None
    _utxos = None

    def __init__(self):
        self._dbConnection = sqlite3.connect("mempool.db")
        self._cursor = self._dbConnection.cursor()
        self._cursor.execute("CREATE TABLE IF NOT EXISTS mempool (opHash TEXT, opRaw TEXT, opTimestamp INT, txFee INT, exectuted INT)")
        self._utxos = utxos.Utxo()
    
    def isValid(self, data):
        # todo: verify signature
        # todo: verify validity
        body = parse_qs(data, keep_blank_values=1)
        if not self._utxos.balance(getAddressFromSignature(data), int(body[b"txFee"][0])):
            return False

        return True
    def hash(self, data):
        body = parse_qs(data, keep_blank_values=1)
        if body[b"operation"][0] == b"STORE":
            # { operation: STORE, source: github_extensions, repos : [], extension : js, signature: "", sender : "", nonce : int, timestamp: int, txFee : int}
            return Web3.sha3(text="%s>%s>%s>%s>%d>%s"%(
                body[b"operation"][0].decode("utf-8"),
                body[b"source"][0].decode("utf-8"),
                str(body[b"repos"]),
                body[b"extension"][0].decode("utf-8"),
                int(body[b"nonce"][0]),
                getAddressFromSignature(data), #todo: replace with extracting user address from signature
            ))


        return "todo"+str(int(time.time()))
        
    def add(self, data):
        raw = data.decode("utf-8")
        body = parse_qs(data, keep_blank_values=1)
        hash = self.hash(data)
        self._cursor.execute("INSERT INTO mempool VALUES('%s', '%s', %d, %d, 0)"%(hash, raw, int(time.time()), int(body[b"txFee"][0])))
        print("Added %s to mempool"%hash)
        return hash
    
    def get(self, count):
        return self._cursor.execute("SELECT * FROM mempool WHERE executed=0 ORDER BY txFee DESC LIMIT %d"%count).fetchall()

    def mark(self, hashes):
        return