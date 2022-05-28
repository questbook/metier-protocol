from concurrent.futures import thread
import sqlite3
import time
import threading
BLOCK_TIME = 10 #seconds

class Blockchain(threading.Thread):
    _dbConnection = None
    _cursor = None
    _mempool = None
    def __init__(self, mempool):
        self._dbConnection = sqlite3.connect("blockchain.db")
        self._cursor = self._dbConnection.cursor()
        self._cursor.execute("CREATE TABLE IF NOT EXISTS blockdata (blocknumber INT, txHash TEXT, data TEXT, output TEXT, status INT)")
        self._cursor.execute("CREATE TABLE IF NOT EXISTS blockheaders (blocknumber INT, blockhash TEXT, confirmations INT, signatures TEXT)")
        self._mempool = mempool
        return

    def run(self):
        self.initHeartbeat()

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
            print("New block time ")
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
