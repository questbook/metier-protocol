import base64
from cgitb import text
from concurrent.futures import thread
from random import random
import eth_account
from numpy import block
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

    _dataSourceHandlers = {}

    def __init__(self, mempool):
        self._dbConnection = psycopg2.connect(database="metieruser", user = "metieruser", password = "metier123", host = "127.0.0.1", port = "5432")
        self._cursor = self._dbConnection.cursor()
        self._cursor.execute("CREATE TABLE IF NOT EXISTS blockdata (blocknumber INT, blockhash TEXT, data TEXT)")
        self._cursor.execute("CREATE TABLE IF NOT EXISTS blockheaders (blocknumber INT, blockhash TEXT, confirmations INT, signatures TEXT, threshold INT)")
        self._mempool = mempool
        self._dataSourceHandlers["github_extensions"] = github_extensions.GithubExtensions()
        return

    def onHeartbeat(self):
        if self.isSelfBlock():
            self.proposeBlock()
        else:
            pass
    
    def onBlockReceived(self, block):
        hash = block["hash"]
        prev = self._cursor.execute("SELECT * FROM blockheaders WHERE blockhash='%s'"%hash)
        if prev:
            print("Already present")
            return None
        data = base64.b64encode(pickle.dumps(block)).hex()
        self._cursor.execute("INSERT INTO blockdata VALUES (%d, '%s','%s')"%(block["number"], hash, data))
        self._cursor.execute("INSERT INTO blockheaders VALUES (%d, '%s', 0, '', %d, %d)"%(block["number"], hash, self.getCurrentStaked(), time.time()))
        print(block["blockTxnsData"])
        print(block)
        blockTransactionsVerification = self.verifyBlockTransactions(pickle.loads(base64.b64decode(bytes.fromhex(block["blockTxnsData"]))))
        onchainTransactionsVerification = True  # todo
        utxosTransactionsVerification = True # todo

        if blockTransactionsVerification and onchainTransactionsVerification and utxosTransactionsVerification:
            confirmation = {
                "hash": hash,
                "accept": 1,
                "signature": web3.Account.sign_message(text="%s/1"%hash).hex()
            }
            requests.post("http://localhost:9000", "operation=BLOCKVALIDATION&confirmation=%s"%base64.b64encode(pickle.dumps(confirmation)).hex())
            pass
    
    def onValidationReceived(self, confirmation):
        hash = confirmation["hash"]
        if confirmation["accept"] == 1:
            blockheadersQuery = self._cursor.execute("SELECT * FROM blockheaders WHERE hash='%s'"%hash)
            if not blockheadersQuery:
                return None
            blockheaders = blockheadersQuery.fetchall()[0]
            number, hash, confirmations, signatures, threshold, timestamp = blockheaders
            if confirmation["signature"] in signatures.split(","):
                return None
            # todo verify threshold at timestamp
            signatures+=confirmation["signature"]+","
            signable = eth_account.messages.encode_defunct(text="%s/1"%hash)
            signer = web3.eth.Account.recover_message(signable, signature=confirmation["signature"])
            confirmations += self.getNodeStake(signer)
            self._cursor.execute("UPDATE blockheaders SET confirmations=%d, signatures='%s' WHERE hash='%s'"%(confirmations, signatures, hash))
            

    def verifyBlockTransactions(self, transactions):
        for txn in transactions:
            print("VERIFYING TXN", txn)
            hash, data, timestamp, fees, output = txn
            body = parse_qs(data, keep_blank_values=1)
            if body["operation"][0] == "STORE":
                if not self._dataSourceHandlers[body["source"][0]].store(data):
                    print("!!! FOUND INVALID TRANSACTION", hash)
                    return False
        return True
                    
            

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
            "blockTxnsData": base64.b64encode(pickle.dumps(blockTxns)).hex(),
            "proposer": proposer,
            "number": blocknumber,
            "signature": "todo"
        }
        print("sending block...")
        requests.post("http://localhost:9000/", "operation=BLOCK&data=%s"%base64.b64encode(pickle.dumps(block)).hex())
        print("sent block")
        return None
    
    def getCurrentStaked(self):
        # todo read from contract
        return 2

    def getNodeStake(self, address):
        # todo read from contract
        return 1