import sqlite3
from time import time

BLOCK_TIME = 10 #seconds

class Blockchain:
    _dbConnection = None
    _cursor = None
    _mempool = None
    def __init__(self, mempool):
        self._dbConnection = sqlite3.connect("blockchain")
        self._cursor = self._dbConnection.cursor()
        self._cursor.execute("CREATE TABLE IF NOT EXISTS blockdata (blocknumber INT, txHash TEXT, data TEXT, output TEXT, status INT)")
        self._cursor.execute("CREATE TABLE IF NOT EXISTS blockheaders (blocknumber INT, blockhash TEXT, confirmations INT, signatures TEXT)")
        self._mempool = mempool
        return

    def initHeartbeat(self):
        while True:
            time.sleep(BLOCK_TIME)
    
    def isSelfBlock(self):
        # check last block
        # check stake on mainnet
        # todo: logic on how to calculate is selfBlock 
        # todo : implement tendermint
        return True
    

    def execute(self, data):
        pass


    def proposeBlock(self):
        txns = self._mempool.get(100)
        block = {}
        return block
