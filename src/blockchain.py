import base64
from cgitb import text
from concurrent.futures import thread
from random import random
import eth_account
import psycopg2
import sys

import time
import threading
from urllib.parse import parse_qs
import pickle
import requests
from pymerkle import MerkleTree

import web3
import datasources.github_extensions as github_extensions
import json
from web3.auto import w3
from eth_account.messages import encode_defunct

config = json.loads(open("./config.json", "r").read())

BLOCK_TIME = 10 #seconds



class Blockchain():
    _dbConnection = None
    _cursor = None
    _mempool = None

    _dataSourceHandlers = {}

    def __init__(self, mempool):
        self._dbConnection = psycopg2.connect(database=config["db"], user = config["db_user"], password = config["db_password"], host = config["host"], port = config["port"])
        self._cursor = self._dbConnection.cursor()
        self._cursor.execute("CREATE TABLE IF NOT EXISTS blockdata (blocknumber INT, blockhash TEXT, data TEXT)")
        self._cursor.execute("CREATE TABLE IF NOT EXISTS blockheaders (blocknumber INT, blockhash TEXT, confirmations INT, signatures TEXT, threshold INT, timestamp INT)")
        self._cursor.execute("SELECT * FROM blockheaders LIMIT 1")
        if self._cursor.rowcount == 0:
            self._cursor.execute("INSERT INTO blockheaders VALUES (0, 'genesis', 1,'', 1,0)")
            self._cursor.execute('''INSERT INTO blockdata VALUES(0,'genesis', '')''')
        self._dbConnection.commit()
        self._mempool = mempool
        self._dataSourceHandlers["github_extensions"] = github_extensions.GithubExtensions()
        return

    def onHeartbeat(self):
        print("Heartbeat received at current block", self.getLatestBlock())
        if self.isSelfBlock():
            self.proposeBlock()
        else:
            pass
    
    def onBlockReceived(self, block):
        hash = block["hash"]
        print("Received block with hash", hash)
        self._cursor.execute("SELECT * FROM blockheaders WHERE blockhash=%s",[hash])
        if self._cursor.rowcount > 0:
            print("Block has already been seen before")
            return None
        data = base64.b64encode(pickle.dumps(block)).hex()
        self._cursor.execute("INSERT INTO blockdata VALUES (%d, '%s','%s')"%(block["number"], hash, data))
        self._cursor.execute("INSERT INTO blockheaders VALUES (%d, '%s', 0, '', %d, %d)"%(block["number"], hash, self.getCurrentThreshold(), time.time()))
        self._dbConnection.commit()
        print("Block added to seen list")
        blockTransactionsVerification = self.verifyBlockTransactions(pickle.loads(base64.b64decode(bytes.fromhex(block["blockTxnsData"]))))
        onchainTransactionsVerification = True  # todo
        utxosTransactionsVerification = True # todo

        if blockTransactionsVerification and onchainTransactionsVerification and utxosTransactionsVerification:
            confirmation = {
                "hash": hash,
                "accept": 1,
                "signature": web3.Account.sign_message(eth_account.messages.encode_defunct(text="%s/1"%hash), config["privateKey"]).signature.hex()
            }
            requests.post("http://localhost:9000", "operation=CONFIRM&data=%s"%base64.b64encode(pickle.dumps(confirmation)).hex())
            pass
    
    def onValidationReceived(self, confirmation):
        print("Confirming...")
        print(confirmation)
        hash = confirmation["hash"]
        if confirmation["accept"] == 1:
            self._cursor.execute("SELECT * FROM blockheaders WHERE blockhash='%s'"%hash)
            if self._cursor.rowcount == 0:
                print("No block with hash %s"%hash)
                return None
            blockheaders = self._cursor.fetchone()
            number, hash, confirmations, signatures, threshold, timestamp = blockheaders
            print("Block headers", hash, confirmations, threshold)
            if confirmation["signature"] in signatures.split(","):
                return None
            # todo verify threshold at timestamp
            signatures+=confirmation["signature"]+","
            signable = eth_account.messages.encode_defunct(text="%s/1"%hash)
            signer = web3.eth.Account.recover_message(signable, signature=confirmation["signature"])
            confirmations += self.getNodeStake(signer)
            self._cursor.execute("UPDATE blockheaders SET confirmations=%d, signatures='%s' WHERE blockhash='%s'"%(confirmations, signatures, hash))
            self._dbConnection.commit()
            print("Confirmations", confirmations, threshold)
            if confirmations >= threshold:
                self._cursor.execute("SELECT * FROM blockdata WHERE blockhash='%s'"%hash)
                blockdata = self._cursor.fetchone()
                blockNumber, blockHash, rawBlock = blockdata
                block = pickle.loads(base64.b64decode(bytes.fromhex(rawBlock)))
                blockTransactions = pickle.loads(base64.b64decode(bytes.fromhex(block["blockTxnsData"])))
                for txn in blockTransactions:
                    hash, data, timestamp, fees, output = txn
                    body = parse_qs(data, keep_blank_values=1)
                    if body["operation"] == "STORE":
                        self._dataSourceHandlers[body["source"]].store(txn)
                    if body["operation"] == "LINKUSER":
                        self._dataSourceHandlers[body["source"]].link(txn)
                print("Confirmed #", confirmation["hash"])
                self._mempool.onTransactionConfirmed(hash)

    def verifyBlockTransactions(self, transactions):
        for txn in transactions:
            hash, data, timestamp, fees, output = txn
            body = parse_qs(data, keep_blank_values=1)
            if body["operation"][0] == "STORE":
                if not self._dataSourceHandlers[body["source"][0]].verify(txn):
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

    def createMerkleTree(self, blockTxns):
        merkleTree = MerkleTree()
        for leaf in blockTxns:
            merkleTree.encrypt(leaf)
        root = merkleTree.get_root_hash()
        return root

    def proposeBlock(self):
        txns = self._mempool.get(100)
        # transactions
        blockTxns = []
        for tx in txns:
            hash, data, timestamp, fees, executed = tx
            body = parse_qs(data, keep_blank_values=1)
            output=''
            if body["operation"][0] == "STORE":
                output = self._dataSourceHandlers[body["source"][0]].fetch(data)
            if body["operation"][0] == "QUERY":
                output = self._dataSourceHandlers[body["source"][0]].query(data)
            blockTxns.append((hash, data, timestamp, fees, output))
            
        blockTxnsHash = self.createMerkleTree(blockTxns) # todo: replace with merkel root
        # todo onchain submissions
        onchainTxnsHash = "n/a"
        # todo : utxos
        utxoTxnsHash = "n/a"

        # todo
        proposer = config["address"]

        blocknumber = self.getLatestBlock() + 1

        blockHash = web3.Web3.sha3(text="%s%s%s%s%d%d"%(blockTxnsHash, onchainTxnsHash, utxoTxnsHash, proposer, blocknumber, int(time.time()))).hex()                    

        block = {
            "hash": blockHash,
            "headers" : [blockTxnsHash, onchainTxnsHash, utxoTxnsHash],
            "blockTxnsData": base64.b64encode(pickle.dumps(blockTxns)).hex(),
            "proposer": proposer,
            "number": blocknumber,
            "signature": w3.eth.account.sign_message(encode_defunct(text=blockHash), private_key=config["privateKey"]).signature.hex()
        }
        requests.post("http://localhost:9000/", "operation=BLOCK&data=%s"%base64.b64encode(pickle.dumps(block)).hex())
        return None
    
    def getCurrentThreshold(self):
        return int(self.getCurrentStaked()/2)

    def getCurrentStaked(self):
        # todo read from contract
        return 2

    def getNodeStake(self, address):
        # todo read from contract
        return 1
    
    def getLatestBlock(self):

        self._cursor.execute("SELECT MAX(blocknumber) FROM blockheaders WHERE confirmations>=threshold")
        if self._cursor.rowcount == 0:
            return 0
        block = self._cursor.fetchone()
        return block[0]
    
    def getBlock(self, blocknumber):
        self._cursor.execute("SELECT * FROM blockheaders WHERE confirmations>=threshold AND blocknumber=%d"%int(blocknumber))
        if self._cursor.rowcount > 0:
            confirmedBlock = self._cursor.fetchone()
            print("Get block", confirmedBlock)
            number, hash, confirmations, signatures, threshold, timestamp = confirmedBlock
            self._cursor.execute("SELECT * FROM blockdata WHERE blockhash='%s'"%hash)
            if self._cursor.rowcount > 0:
                blockData = self._cursor.fetchone()
                number, hash, data = blockData
                block = pickle.loads(base64.b64decode(bytes.fromhex(data)))
                blockTransactions = pickle.loads(base64.b64decode(bytes.fromhex(block["blockTxnsData"])))
                onchainTransactions = []
                utxoTransactions = []
                return {
                    "hash": hash, 
                    "confirmations": confirmations,
                    "threshold": threshold,
                    "signatures": signatures,
                    "blockTransactions": blockTransactions,
                    "onchainTransactions": onchainTransactions,
                    "utxoTransactions": utxoTransactions
                }

