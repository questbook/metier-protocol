import web3

def getAddressFromSignature(data) :
    # todo: web3.ecrecover
    address = web3.eth.accounts.recover(data)
    return "address"