from Crypto.Cipher import AES
import Crypto.Util.Padding  as Padding
import random
import string
import base64

'''
#data = input("Input plaintext to encrypt: ")

#cleaning up data
c = len(data)%16
if c != 0:
    data = Padding.pad(bytes(data,"utf-8"), 16)
else:
    data = bytes(data, "utf-8")
'''

def generateKey():
    lenBytes = 32
    #generating key and saving it to file
    key = ''.join(random.choice(string.ascii_letters) for i in range(lenBytes))
    key = bytes(key,"utf8")
    fileO = open("key.txt","wb")
    fileO.write(key)
    fileO.close()
    #print("\nGenerated key: " + str(key))
    return key

def loadKey():
    fileO = open("key.txt","rb")
    key = fileO.readline()
    fileO.close()
    #print("\nLoaded key: " + str(key))
    return key

def encryptText(data, key):
    c = len(data)%16
    data = Padding.pad(bytes(data,"utf-8"), 16)
    cipher = AES.new(key, AES.MODE_ECB)
    ciphertext = cipher.encrypt(data)
    ciphertext = base64.b64encode(ciphertext) #encoding ciphertext to BASE64
    ciphertext = ciphertext.decode('utf-8')
    return ciphertext

def decryptText(data, key):
    cipher = AES.new(key, AES.MODE_ECB)
    data = data.encode('utf-8')
    data = base64.b64decode(data)#decoding ciphertext from BASE64
    plaintext = cipher.decrypt(data)
    plaintext = Padding.unpad(plaintext, 16)
    plaintext = plaintext.decode('utf-8')
    return plaintext


