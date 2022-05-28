import psycopg2

class Utxo : 
    _dbConnection = None
    _cursor = None
    def __init__(self):
        self._dbConnection = psycopg2.connect(database="metieruser", user = "metieruser", password = "metier123", host = "127.0.0.1", port = "5432")
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