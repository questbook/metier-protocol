import base64
from concurrent.futures import thread
from random import random
import psycopg2

import time
import threading
from urllib.parse import parse_qs
import pickle
import requests

import web3
import datasources.github_extensions as github_extensions
BLOCK_TIME = 10 #seconds

class Blockchain():
    _dbConnection = None
    _cursor = None
    _mempool = None
    def __init__(self, mempool):
        self._dbConnection = psycopg2.connect(database="metieruser", user = "metieruser", password = "metier123", host = "127.0.0.1", port = "5432")
        self._cursor = self._dbConnection.cursor()
        self._cursor.execute("CREATE TABLE IF NOT EXISTS blockdata (blocknumber INT, txHash TEXT, data TEXT, output TEXT, status INT)")
        self._cursor.execute("CREATE TABLE IF NOT EXISTS blockheaders (blocknumber INT, blockhash TEXT, confirmations INT, signatures TEXT)")
        self._mempool = mempool
        return

    def onHeartbeat(self):
        if self.isSelfBlock():
            self.proposeBlock()
        else:
            pass

    def isSelfBlock(self):
        # check last block
        # check stake on mainnet
        # todo: logic on how to calculate is selfBlock 
        # todo : implement tendermint
        r = int(random() * 1000)
        return (r%2) == 0
    

    def execute(self, data):
        pass


    def proposeBlock(self):
        txns = self._mempool.get(100)
        print(txns)
        # transactions
        blockTxns = []
        for tx in txns:
            hash, data, timestamp, fees, executed = tx
            body = parse_qs(data, keep_blank_values=1)
            if body["operation"][0] == "STORE":
                if body["source"][0] == "github_extensions":
                    githubExtensions = github_extensions.GithubExtensions()
                    output = githubExtensions.fetch(data)
                    blockTxns.append((hash, data, timestamp, fees, output))
        print("blocktxns", blockTxns)
        blockTxnsHash = web3.Web3.sha3(pickle.dumps(blockTxns)).hex() # todo: replace with merkel root
        print("blockTxnsHash", blockTxnsHash)
        # todo onchain submissions
        onchainTxnsHash = "n/a"
        # todo : utxos
        utxoTxnsHash = "n/a"

        # todo
        proposer = "n/a"
        #todo 
        blocknumber = 0

        blockHash = web3.Web3.sha3(text="%s%s%s%s%d"%(blockTxnsHash, onchainTxnsHash, utxoTxnsHash, proposer, blocknumber)).hex()                    
        print("blockHash", blockHash)

        block = {
            "hash": blockHash,
            "headers" : [blockTxnsHash, onchainTxnsHash, utxoTxnsHash],
            "blockTxnsData": base64.b64encode(pickle.dumps(blockTxns)),
            "proposer": proposer,
            "blocknumber": blocknumber,
            "signature": "todo"
        }
        print("sending block...")
        requests.post("http://localhost:9000/", "operation=BLOCK&data=%s"%base64.b64encode(pickle.dumps(block)))
        print("sent block")
        return None
