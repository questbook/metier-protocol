import web3

def getAddressFromSignature(data, signature) :
    signature = signature
    signable = data
    signer = web3.eth.Account.recover_message(signable, signature)
    return signer