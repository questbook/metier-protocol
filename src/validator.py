import sqlite3

class Validator:
    def __init__(self):
        return 
    
    def processStore(self, data):
        pass

    def processQuery(self, data):
        pass

    def processChallenge(self, data):
        pass

    def processResonse(self, data):
        pass

    def processBlock(self, data):
        pass

    def processSubmission(self, data):
        pass

    
    def isSelfBlock(self):
        # return hash(last block hash, block number + 1 ) == myAddress()
        pass

    def processTxn(self):
        # identify as store/query/... call appropriate function
        # return txn hash of output
        pass
        

    def validateBlock(self, data):
        # iterate on all transactions and process
        # for tx in data.txns:
        #   require processTxn(tx.data) == tx.hash
        # validate correctness of data.finTxns (utxos)
        pass

    def createBlock(self, data):
        # pick top N transactions from mempool
        # for tx: 
        #   add to merkel tree (x)
        # update utxos for added txs
        # block hash = hash (merkel(tx), merkel(utxo))
        # return (hash, block number, block data)
        return 
    
    def addBlockValidation(self, data):
        # others signoff on blocks
        return
    
    