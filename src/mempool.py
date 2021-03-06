from cgitb import text
import sys
import psycopg2
from urllib.parse import parse_qs
from web3 import Web3
import web3
from utils import getAddressFromSignature
import utxos
import eth_account
from time import time

class Mempool :
    _dbConnection = None
    _cursor = None
    _utxos = None

    def __init__(self):
        self._dbConnection = psycopg2.connect(database="metieruser", user = "metieruser", password = "metier123", host = "127.0.0.1", port = "5432")
        self._cursor = self._dbConnection.cursor()
        self._cursor.execute("CREATE TABLE IF NOT EXISTS mempool (opHash TEXT, opRaw TEXT, opTimestamp INT, txFee INT, executed INT)")
        self._dbConnection.commit()
        self._utxos = utxos.Utxo()
    
    def isValid(self, data):
        body = parse_qs(data, keep_blank_values=1)

        # todo: verify validity
        signableText, signature = data.decode("utf-8").split("&signature=")
        signerClaimed = body[b"address"][0].decode("utf-8")
        signable = eth_account.messages.encode_defunct(text=signableText)
        signerSigned = web3.eth.Account.recover_message(signable, signature=signature)
        if not signerClaimed==signerSigned:
            print("Invalid signature")
            return False
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
            )).hex()


        return "todo"+str(int(time()))
        
    def add(self, data):
        print("Adding to mempool", data)
        if not self.isValid(data):
            print("invalid transaction, not adding to mempool")
            return None
        print("valid transaction")
        raw = data.decode("utf-8")
        body = parse_qs(data, keep_blank_values=1)
        hash = self.hash(data)
        self._cursor.execute("SELECT * FROM mempool WHERE opHash='%s'"%hash)
        if self._cursor.rowcount > 0:
            return None
        print("Pushing to mempool")
        self._cursor.execute("INSERT INTO mempool VALUES('%s', '%s', %d, %d, 0)"%(hash, raw, int(time()), int(body[b"txFee"][0])))
        self._dbConnection.commit()
        print("Pushed to mempool with hash", hash)
        return hash
    
    def get(self, count):
        self._cursor.execute("SELECT * FROM mempool WHERE executed=0 ORDER BY txFee DESC LIMIT %d"%count)
        if self._cursor.rowcount == 0 : 
            return []
        return self._cursor.fetchall()

    def onTransactionConfirmed(self, hash):
        self._cursor.execute("UPDATE mempool SET executed=1 WHERE opHash='%s'"%hash)
        self._dbConnection.commit()
        return