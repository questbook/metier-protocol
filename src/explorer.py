from blockchain import Blockchain


class Explorer:
    _blockchain = None
    _mempool = None
    def __init__(self, blockchain, mempool):
        self._blockchain = blockchain
        self._mempool = mempool
        return
    
    def query(self, path):
        if path.startswith("/blocks") :
            parts = path.split("/")
            blockNumber = parts[2]
            if blockNumber == "latest":
                blockNumber = self._blockchain.getLatestBlock()
            block = self._blockchain.getBlock(blockNumber)
            html  = "<html>"
            html += "  <h1> Block "+str(blockNumber) +"</h1>"
            html += "  <p> Confirmations %d out of %d </p>"%(block["confirmations"], block["threshold"])
            html += "  <h2> Block Transactions : </h2>"
            for transaction in block["blockTransactions"]:
                html += "<h3> Transaction #%s </h3>"%transaction[0]
                html += "<pre>%s</pre>"%str(transaction)
            html += "  <p> Transactions that need consensus on the data retreived </p>"
            html += "  <h2> Callback Transactions : </h2>"
            html += "  <p> Transactions that require a callback to the calling smart contract that uses has_credential</p>"
            html += "  <h2> UTXO Transactions </h2>"
            html += "  <p> Transactions that alter the financial balances in $CRED </p>"
            html += ""
            html += "</html>"
            return html
        return "<html><h1>Error</h1><p>Unknown path %s</p></html>"%path