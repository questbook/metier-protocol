import base64
import pickle
from urllib.parse import parse_qs
import psycopg2
from web3 import Web3

class GithubExtensions:
    _dbConnection = None
    _cursor = None

    def __init__(self):
        self._dbConnection = psycopg2.connect(database="metieruser", user = "metieruser", password = "metier123", host = "127.0.0.1", port = "5432")
        self._cursor = self._dbConnection.cursor()
        self._cursor.execute("CREATE TABLE IF NOT EXISTS github_extensions (id SERIAL PRIMARY KEY, credential TEXT, github_username TEXT)")
        self._cursor.execute("CREATE TABLE IF NOT EXISTS github_username_address_mappings (github_username TEXT, address TEXT)")
        self._dbConnection.commit()
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
        return base64.b64encode(pickled).hex()
    
    def verify(self, txn):
        hash, data, timestamp, fees, output = txn
        print("Verifying(seen)", self.fetch(data))
        print("Verifying(claimed)", output)

        seenResponseHash = Web3.sha3(text=self.fetch(data)).hex()
        claimedResponseHash =  Web3.sha3(text=output).hex()
        print("CHECKING STORE: ", seenResponseHash, claimedResponseHash)
        return seenResponseHash == claimedResponseHash
    
    def store(self, txn):
        hash, data, timestamp, fees, output = txn
        body = parse_qs(data, keep_blank_values=1)
        signature = body["signature"][0] 
        address = str(body["address"][0]) # todo extract address from signature
        storable = pickle.loads(base64.b64decode(bytes.fromhex(output)))
        for member in storable.members:
            self._cursor.execute("INSERT INTO github_extensions VALUES (0, '%s','%s')"%("%s:%s"%(address,hash), member[0]))
            self._dbConnection.commit()
        return 
    
    def getUsernameFromAuthToken(self, authToken):
        #todo request githubapi
        return authToken 

    def link(self, data):
        # todo : extract from access token
        body = parse_qs(data, keep_blank_values=1)
        address = body["address"] # todo : extract from signature
        username = self.getUsernameFromAuthToken(body["auth_token"])
        self._cursor.execute("SELECT * FROM github_username_address_mappings WHERE github_username='%s'"%username)
        if self._cursor.rowcount == 0 :
            self._cursor.execute("UPDATE github_username_address_mappings SET address='%s' WHERE github_username='%s'"%(address, username))
            self._dbConnection.commit()
        else:
            self._cursor.execute("INSERT INTO github_username_address_mappings VALUES ('%s','%s')"%(username, address))
            self._dbConnection.commit()
        return

    def query(self, data):
        body = parse_qs(data, keep_blank_values=1)
        address = body["address"][0]
        credential = body["credential"][0]
        self._cursor.execute("SELECT * FROM github_extensions INNER JOIN github_username_address_mappings ON github_extensions.github_username=github_username_address_mappings.github_username WHERE github_username_address_mappings.address='%s'"%address)
        if self._cursor.rowcount == 0:
            return []
        return self._cursor.fetchall()