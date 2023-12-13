
import MyAES
import MyHash
import os
import re
import mysql.connector as mySQLDB
import time
import pathlib
import random
import string
import base64
import nltk
from nltk.corpus import stopwords

def cls(): #command line clearing, purely estetic
    os.system('cls' if os.name=='nt' else 'clear')

#--------------------------Predefinitions of Global Variables and DB setup Start----------------------------

databaseName = "SSE_extended_example" #Change this to use different database

startTime = 0

EncKeyLength = 32

#local file path preparation
rootPath = pathlib.Path.cwd()
txtFileLocation1 = rootPath / 'dataset' #choice of dataset
txtFileLocation2 = rootPath / 'CSP'
txtFileLocation3 = rootPath / 'User'
txtFileLocation4 = rootPath / 'Owner'
txtFileLocationTA = rootPath / 'TA.txt'
txtFileLocationCSP = rootPath / 'CSP.txt'

if not txtFileLocation1.exists():
    raise Exception("Dataset not supplied. Double check variable txtFileLocation1 and working folder for dataset")

if not txtFileLocation2.exists():
    txtFileLocation2.mkdir()

if not txtFileLocation3.exists():
    txtFileLocation3.mkdir()

if not txtFileLocation4.exists():
    txtFileLocation4.mkdir()

#stopword preparation
nltk.download('stopwords')
nltkStops = stopwords.words('english')
#print(nltk_stops)

#mySQL login information and cursor initialization
mydb = mySQLDB.connect(
  host="localhost",
  user="root",
  password="abc123",
  allow_local_infile=True
)
mycursor = mydb.cursor()
#Creates database and tables itself! Change as necessary
mycursor.execute("CREATE DATABASE IF NOT EXISTS {};".format(databaseName))
mycursor.execute("USE {};".format(databaseName))
mycursor.execute("SET GLOBAL local_infile = 1;")
mycursor.execute("CREATE TABLE IF NOT EXISTS csp_keywords (csp_keyword VARCHAR(50) PRIMARY KEY, csp_val VARCHAR(25));")
mycursor.execute("CREATE TABLE IF NOT EXISTS ta_keywords (ta_keyword VARCHAR(50) PRIMARY KEY, ta_keyword_nofiles INT, ta_keyword_nosearch INT);")

#--------------------------Predefinitions of Global Variables and DB setup End----------------------------

#--------------------------Extra Functions Start----------------------------

#Getting keyword values from TA at the start of a search
def GetValuesTA(hash):
    try:
        mycursor.execute("SELECT ta_keyword_nosearch FROM ta_keywords WHERE ta_keyword = '{}'".format(hash))
        numsearch = mycursor.fetchone()
        numsearch = str(numsearch)
        numsearch = numsearch.replace("(", "")
        numsearch = numsearch.replace(")", "")
        numsearch = numsearch.replace(",", "")
        mycursor.execute("SELECT ta_keyword_nofiles FROM ta_keywords WHERE ta_keyword = '{}'".format(hash))
        numfiles = mycursor.fetchone()
        numfiles = str(numfiles)
        numfiles = numfiles.replace("(", "")
        numfiles = numfiles.replace(")", "")
        numfiles = numfiles.replace(",", "")
    except:
        numfiles = -1
        numsearch = -1
    if (numfiles == 'None'):
        numfiles = -1
        numsearch = -1
    return int(numfiles), int(numsearch)

#Getting file paths from CSP after successful search
def GetFilesCSP(Kw, noFiles, filesToSend, Lu):
    #print(Lu)
    for i in range(1,noFiles+1):
        forAddr = Kw+str(i)
        forAddr = forAddr.encode('utf-8')
        addr = MyHash.hashText(forAddr)
        mycursor.execute("SELECT csp_val FROM csp_keywords WHERE csp_keyword = '{}'".format(addr))
        file = mycursor.fetchone()
        mycursor.execute("UPDATE csp_keywords SET csp_keyword = '{}' WHERE csp_keyword = '{}'".format(Lu[i-1], addr))
        file = str(file)
        #print(addr)
        #print(Lu[i-1])
        #print(file)
        if file != 'None':
            file = file.replace("(", "")
            file = file.replace(")", "")
            file = file.replace(",", "")
            filesToSend.append(file)

#decrypting files after successful search
def DecryptFiles(filesToSend, user):
    key = LoadKeyCSP()
    for i in range(0, len(filesToSend)):
        filePathI = txtFileLocation2 / filesToSend[i]
        if user == 0:
            filePathO = txtFileLocation3 / filesToSend[i]
        else:
            filePathO = txtFileLocation4 / filesToSend[i]
        fileI = open(filePathI, 'r')
        fileO = open(filePathO, 'w', encoding="utf8")
        cipherText = fileI.read()
        fileI.close()
        plaintext = MyAES.decryptText(cipherText, key)
        fileO.write(plaintext)
        fileO.close()

#encrypting files after database upload
def EncryptFiles(fileName,text):
    key = LoadKeyCSP()
    filePathO = txtFileLocation2 / fileName
    fileO = open(filePathO, 'w')
    ciphertext = MyAES.encryptText(text, key)
    fileO.write(ciphertext)
    fileO.close() 
 
#Simulate sending the data to the CSP 
def SendCSP(Kw, noFiles, Lu):
    Lta = ForwardTA(Kw, noFiles) #forwards the data to TA to validate data
    K = LoadKeyCSP()
    filesToSend = []
    if(Lta == Lu): #check if TA values match with the users values
        GetFilesCSP(Kw, noFiles, filesToSend, Lu)
        output = 1
    else:
        output = -1
    if output != -1:
        for i in range(0,len(filesToSend)):
            filesToSend[i] = MyAES.decryptText(filesToSend[i], K)
            filesToSend[i] = re.sub("([\d]+$)","",filesToSend[i])
        #print(filesToSend)
        DecryptFiles(filesToSend, 0)
    SendACK(output, Kw) #send acknowledgment to update tables

#Forwarding initial information to the TA for confimation
def ForwardTA(Kw, noFiles):
    keyTA = LoadKeyTA()    
    decrypted = MyAES.decryptText(Kw, keyTA)
    lengthInfo = len(decrypted)
    hash = decrypted[0:lengthInfo-1]
    noSearch = int(decrypted[lengthInfo-1:])
    noSearch += 1
    KwNext = MyAES.encryptText(hash+str(noSearch), keyTA)
    Lta = []
    for i in range(1,noFiles+1):
        forAddr = KwNext+str(i)
        forAddr = forAddr.encode('utf-8')
        addr = MyHash.hashText(forAddr)
        Lta.append(addr)
    return Lta 

#Simulate sending acknowledgment of successful/failed run to the TA/DataOwner
def SendACK(param, Kw):
    if (param == 1):
        keyTA = LoadKeyTA()
        decrypted = MyAES.decryptText(Kw, keyTA)
        lengthInfo = len(decrypted)
        hash = decrypted[0:lengthInfo-1]
        mycursor.execute("SELECT ta_keyword_nosearch FROM ta_keywords WHERE ta_keyword = '{}'".format(hash)) #fetches old value
        numsearch = mycursor.fetchone()
        numsearch = str(numsearch)
        numsearch = numsearch.replace("(", "")
        numsearch = numsearch.replace(")", "")
        numsearch = int(numsearch.replace(",", ""))
        numsearch += 1
        mycursor.execute("UPDATE ta_keywords SET ta_keyword_nosearch = '{}' WHERE ta_keyword = '{}'".format(numsearch, hash)) #updates it
        mydb.commit() 
    else:
        print("Intrusion detected, request failed");

#load both keys for the Data Owner 
def LoadKey():
    fileO = open("keys.txt","rb")
    keys = fileO.readline()
    fileO.close()
    #print("\nLoaded key: " + str(key))
    return keys 

#loading the TA's key
def LoadKeyTA():
    fileO = open("keys.txt","rb")
    key = fileO.read(32)
    fileO.close()
    #print("\nLoaded key: " + str(key))
    return key 

#loading the CSP's key
def LoadKeyCSP():
    fileO = open("keys.txt","rb")
    fileO.read(32)
    key = fileO.read(32)
    fileO.close()
    #print("\nLoaded key: " + str(key))
    return key 

#Upload all gathered info to DB tables
def UploadToDB(inTA, inCSP, searchValue, K, startTime):
    #decrypting values
    searchValue = MyAES.decryptText(searchValue, K)
    for keyValue in inTA:
        inTA[keyValue] = int(MyAES.decryptText(inTA[keyValue],K))
    #writing to local files
    fileTA = open(txtFileLocationTA,"w")
    fileCSP = open(txtFileLocationCSP,"w")
    for key in inTA:
        fileTA.write("{},{},{}\n".format(key, inTA[key], searchValue))
    i = 0
    j = 0
    for key in inCSP:
        fileCSP.write("{},{}\n".format(key, inCSP[key]))
    fileTA.close()
    fileCSP.close()
    #loading local files to upload information to database tables
    query = "LOAD DATA LOCAL INFILE '{}' INTO TABLE ta_keywords FIELDS TERMINATED BY ',';".format(txtFileLocationTA)
    query = query.replace("\\","/")
    mycursor.execute(query)
    mydb.commit()
    print("Time to index, make local copies and upload to TA: {}".format(time.time()-startTime))
    query = "LOAD DATA LOCAL INFILE '{}' INTO TABLE csp_keywords FIELDS TERMINATED BY ',';".format(txtFileLocationCSP)
    query = query.replace("\\","/")
    mycursor.execute(query)
    mydb.commit()
    #for keyValue in inCSP: old functions; not in use
        #mycursor.execute("INSERT INTO csp_keywords(csp_keyword, csp_val) value ('{}', '{}')".format(keyValue, inCSP[keyValue]))
    #for keyValue in inCSP:
    #    mycursor.execute("INSERT INTO csp_keywords(csp_keyword, csp_val) value ('{}', '{}')".format(keyValue, inCSP[keyValue]))
    #mydb.commit()

#removes stopwords in text
def StopWordRemoval(fileText):
    for i in range (0, len(nltkStops)):
        fileText = fileText.replace(" {} ".format(nltkStops[i]), " ") #find the word and replace it with a blank space
    return fileText


#--------------------------Extra Functions End-----------------------------

#--------------------------Main Functions Start----------------------------

#Key Generation function
def KeyGen(keyLen):
    #generating key and saving it to file
    key_TA = ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(keyLen)) #generate TA key with random symbols
    key_SKE = ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(keyLen)) #generate CSP key with random symbols
    key_TA = bytes(key_TA,"utf8")
    key_SKE = bytes(key_SKE,"utf8")
    fileO = open("keys.txt","wb") #saving key for later use and testing
    fileO.write(key_TA+key_SKE)
    fileO.close()
    return key_TA+key_SKE

#Index Generation function
def InGen(K):
    #initializing dictionaries and file locations
    input_data_TA = {}
    input_data_CSP = {}
    fileList = os.listdir(txtFileLocation1)
    #print(fileList)
    startTime = time.time()
    for i in range(0,len(fileList)):
        #text preperation
        filePath = txtFileLocation1 / fileList[i]
        fileI = open(filePath,"r",encoding = "utf8")
        fileTextOrg = fileI.read()
        fileI.close()
        fileText = re.sub("[^a-zA-Z \n]+", "", fileTextOrg)
        fileText = fileText.lower()
        fileText = StopWordRemoval(fileText)
        splitText = re.split(' ',fileText)
        #indexing begins
        print("File {} of {} started".format(i+1, len(fileList)))
        input_data_CSP, input_data_TA = AddFile(K, splitText, input_data_TA, input_data_CSP, fileList[i])
        EncryptFiles(fileList[i], fileTextOrg)
        print("File {} of {} done".format(i+1, len(fileList)))  
        #resetting for memory reasons
        fileText = ""
        fileTextOrg = ""
        splitText = []
    print("Starting DB upload")
    for keyValue in input_data_TA:
        input_data_TA[keyValue] = MyAES.encryptText(str(input_data_TA[keyValue]),K[0:32])#data is encrypted
    searchValueInit = MyAES.encryptText("0",K[0:32])
    print("Uploading {} files to the TA".format(len(input_data_TA)))
    print("Uploading {} files to the CSP".format(len(input_data_CSP)))
    UploadToDB(input_data_TA, input_data_CSP,searchValueInit, K[0:32], startTime) #sent to upload to DB
    print("Uploading finished")
    wholeTime = time.time() - startTime
    print("Time to add to CSP in seconds: {}".format(wholeTime))

#Data preperation for uploading function
def AddFile(K, tarp, inTA, inCSP, filename):
    wordArray = {} # initialize found word array
    for j in range(0,len(tarp)):
        tarp[j] = tarp[j].encode('utf-8')
        hash = MyHash.hashText(tarp[j])
        try: 
            wordArray[hash] = wordArray[hash]+0 #try to change value in dictionary
        except KeyError: #value does not exist. That means first time seeing word
            wordArray[hash] = 0 #add the new word to the temporary dictionary as the key to the dictionary with an arbitrary value
            Kw = MyAES.encryptText(hash+'0', K[0:32])
            try:
                inTA[hash] = inTA[hash]+1 #do the word repetition in a file count
            except KeyError:
                inTA[hash] = 1 # if word does not exist create it 
            forAddr = Kw+str(inTA[hash])
            forAddr = forAddr.encode('utf-8')
            addr = MyHash.hashText(forAddr)
            val = MyAES.encryptText(filename+str(inTA[hash]),K[32:64])
            inCSP[addr] = val
    wordArray = {} # refresh word array for memory
    return inCSP, inTA

#Searching through DB function
def Search(K, w):
    #preparing all necessary values
    startTime = time.time()
    w = w.lower()
    hash = MyHash.hashText(w.encode('utf-8'))
    noFiles, noSearch = GetValuesTA(hash) #requesting hash values from TA table
    try:
        print("Amount of files found: {}".format(int(noFiles)))
        Kw = MyAES.encryptText(hash+str(noSearch), K[0:32])
        noSearch += 1
        KwNext = MyAES.encryptText(hash+str(noSearch), K[0:32]) #creating needed values for check
        objListU = []
        for i in range(1,noFiles+1):
            forAddr = KwNext+str(i)
            forAddr = forAddr.encode('utf-8')
            addr = MyHash.hashText(forAddr) #creating addr list
            #addr = MyAES.encryptText(str(i),bytes(KwNext[len(KwNext)-32:], 'utf-8'))
            objListU.append(addr)
        SendCSP(Kw, noFiles,objListU) # sending request to CSP 
        output = 1
        print("Time to search for inputted word: {}".format(time.time()-startTime))
    except:
        print("No files found with inputted word.")
        output = -1
    return output


#--------------------------Main Functions End-----------------------------
cls()
print("Welcome!\n1 - Generate new keys\n2 - Load prior session keys")   
print("Generating new keys will overwrite prior keys")
while 1:
    x = input("Choose action: ")
    cls()
    if(x == "1"):
        keys = KeyGen(EncKeyLength) #Generating Keys
        print("Keys generated")
        break
    elif (x == "2"):
        keys = LoadKey() #Loading prior keys
        print("Keys loaded")
        break
    else:
        print("Invalid input")
        print("1 - Generate new keys\n2 - Load prior session keys")
        print("Generating new keys will overwrite prior keys")
#keys[0:32]key TA; keys[32:64]key SKE
while(1):
    if(x == 1):
        print("New keys generated. Anything uploaded with prior keys will be unrecognizable.")
    print("1 - Generate indexes and upload files\n2 - Search for a word\n3 - Delete ALL previous database entries?")
    x = input("Choose action: ")
    if(x == "1"):
        #mycursor.execute("DROP DATABASE {};".format(databaseName))
        #mycursor.execute("CREATE DATABASE IF NOT EXISTS {};".format(databaseName))
        #mycursor.execute("USE {};".format(databaseName))
        #mycursor.execute("SET GLOBAL local_infile = 1;")
        #mycursor.execute("CREATE TABLE IF NOT EXISTS csp_keywords (csp_keyword VARCHAR(50) PRIMARY KEY, csp_val VARCHAR(25));")
        #mycursor.execute("CREATE TABLE IF NOT EXISTS ta_keywords (ta_keyword VARCHAR(50) PRIMARY KEY, ta_keyword_nofiles INT, ta_keyword_nosearch INT);")
        InGen(keys) #start Index Generation
        print("Continue with program? 1 - Yes; 2 - No")
        x = int(input("Choose action: "))
        if(x == 2):
            print("Thank you for using this program")
            break
        x = 0
        cls()
    elif(x=="2"):
        searchWord = input("Type in the search word: ")
        output = Search(keys, searchWord) #start Search Function
        if(output == 1):
            print("Search complete, files decrypted")
        else:
            print("Search failed, files with such a word do not exist")
        print("Continue with program? 1 - Yes; 2 - No")
        x = int(input("Choose action: "))
        if(x == 2):
            print("Thank you for using this program")
            break
        x = 0
        cls()
    elif(x=="3"):
        mycursor.execute("DROP DATABASE {};".format(databaseName))
        mycursor.execute("CREATE DATABASE IF NOT EXISTS {};".format(databaseName))
        mycursor.execute("USE {};".format(databaseName))
        mycursor.execute("SET GLOBAL local_infile = 1;")
        mycursor.execute("CREATE TABLE IF NOT EXISTS csp_keywords (csp_keyword VARCHAR(50) PRIMARY KEY, csp_val VARCHAR(25));")
        mycursor.execute("CREATE TABLE IF NOT EXISTS ta_keywords (ta_keyword VARCHAR(50) PRIMARY KEY, ta_keyword_nofiles INT, ta_keyword_nosearch INT);")
        cls()
        print("Previous tables deleted")
    else:
        print("Invalid Input.")