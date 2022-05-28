import base64
import pickle

class GithubExtensions:
    def __init__(self):
        pass

    def fetch(self, data):
        # todo : replace with real fetch
        response = {
            "credential": "dummy",
            "repo": "madhavanmalolan/ecm.js",
            "ext": ".js",
            "members": [("user1", 0), ("user2", 0)]
        }
        pickled = pickle.dumps(response)
        return base64.b64encode(pickled)
    
    def store(self, data):
        # todo : check output before storing 
        return True
    
    def query(self, data):
        return {}
