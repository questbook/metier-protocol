import sqlite3

class Utxo : 
    _dbConnection = None
    _cursor = None
    def __init__(self):
        self._dbConnection = sqlite3.connect("utxos.db")
        self._cursor = self._dbConnection.cursor()

    def balance(self, address, amount):
        # todo check if balance exists
        return True
    
    def mint(self, address, amount):
        # todo: create new utxo
        return 
    
    def spend(self, fromAddress, toAddress, amount):
        if not self.balance(fromAddress, amount):
            return 
        # todo: get utxos and create new utxos
        return
    
    def revert(toBlock) :
        # mark all utxos block>toBlock as orphans
        return 