import hashlib
import hmac
import base64 as b64

def hashText(paraText):
    #prepare the hashing tool and get text from file
    hasher = hashlib.sha256()
    hasher.update(paraText)

    #get the digest of the text
    sign = hasher.digest()
    sign = b64.b64encode(sign)
    sign = sign.decode("utf-8") 
    return sign

