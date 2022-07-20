import re
import mysql.connector

from scrapeUtils import pushToDatabases, wordAlreadyStored, getInfoFromWord, wordIsAmbiguous, \
    wordIsInterjection, wordStartsWithCapitalLetter, wordHasUnexpectedCharacters, \
    pushToExceptionWordsTable, processWord, idAlreadyStored, getIdOfWord, punctuations

conn = mysql.connector.connect(host="127.0.0.1", user="root", password="", database="hanapsalita")
cur = conn.cursor()

lastRowId = None
jsonDatabase = ""
wordsJsonFilename = ""
category = "C"

verbSet = {}

for verbBaseForm, wordList in verbSet.items():
    verbBaseForm = verbBaseForm.strip()
    for word in wordList:
        word = word.strip()
        if not wordAlreadyStored(cur, "tagalog_words", word):
            processWord(word, conn, cur, jsonDatabase, wordsJsonFilename, lastRowId, category, verbBaseForm)

cur.close()
conn.close()







