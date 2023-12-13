A more in-depth example of an SSE scheme being used for secure storage and encrypted searching in databases.

Needed Python libraries:
regex (v. 2020.11.13)
mysql-connector-python (v. 8.0.26)
nltk (v. 3.5)
pycryptodome (v. 3.10.1)

For database storage MySQL Server 8.0.26 with InnoDB was used. Default setting were used aside for the global variable local_infile being changed to 'ON'. Inspection of the database was done through MySQL Workbench 8.0.27

Dataset used https://zenodo.org/records/3360392

Use instructions:
0. Edit the code to setup correct login to the database by changing username and password (lines 54-56 in variable mydb)

1. Launch the program
The program can be launched through a command line by running the command "python SSE_Example.py" or by using Visual Studio to open the code (by adding all 3 python files: SSE_Example.py, MyAES.py and MyHash.py).

2. Select either generating keys (1) or loading previous keys (2)
Generating keys will require the entire indexing upload process to run again as all prior values in the CSP table will be unreadable (time it take: ~1h20min for the smallest database depending on computer specifications)

3. Select either Index Generation (1) or Search (2) when prompted

3.1. Index Generation will automatically select to generate inputs from the folder /dataset/ unless specified otherwise in the code (variable to change txtFileLocation1 on line 28). After the indexes are generated and the values are ready to be uploaded to the database the program will encrypt all files in the specified folder and save them in /CSP/ (variable to change txtFileLocation2 on line 27)

3.2. Search function will prompt you to input a word, which will be hashed and searched for in the databases after which all files found that contain the word will be decrypted and placed in folder /Users/ unless specified otherwise (variable to change txtFileLocation3 on line 28)

4. The program will ask if the user wants to continue using the program. Choose either Yes (1) to restart from step 3 or No (2) to finish the program and close it.