import base64
import pickle
from urllib.parse import parse_qs
from web3 import Web3

class GithubExtensions:
    def __init__(self):
        pass

    def fetch(self, data):
        # todo : replace with real fetch
        body = parse_qs(data, keep_blank_values=1)

        response = {
            "credential": "dummy",
            "repo": "madhavanmalolan/ecm.js",
            "ext": ".js",
            "members": [("user1", 0), ("user2", 0)]
        }
        pickled = pickle.dumps(response)
        return base64.b64encode(pickled)
    
    def store(self, txn):
        hash, data, timestamp, fees, output = txn
        seenResponseHash = Web3.sha3(text=base64.b64encode(pickle.loads(self.fetch(data))).hex()).hex()
        claimedResponseHash =  Web3.sha3(text=base64.b64encode(pickle.loads(output)).hex()).hex()
        print("CHECKING STORE: ", seenResponseHash, claimedResponseHash)
        
        return seenResponseHash == claimedResponseHash
    
    def query(self, data):
        return {}
