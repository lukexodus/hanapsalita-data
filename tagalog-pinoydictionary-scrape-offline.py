import re

import mysql.connector

from scrapeUtils import pushToDatabases, wordAlreadyStored, getInfoFromWord, wordIsAmbiguous, \
    wordIsInterjection, wordStartsWithCapitalLetter, wordHasUnexpectedCharacters, \
    pushToExceptionWordsTable, processWord, pushToMySQL

file = open("wordsToBeIncluded.txt")
wordsLists = file.readlines()

conn = mysql.connector.connect(host="127.0.0.1", user="root", password="", database="hanapsalita")
cur = conn.cursor()

lastRowId = None

for word in wordsLists:
    word = word.strip()
    category = "NV"  # Non-Verb

    verbBaseForm = None

    if not word:
        continue
    elif wordHasUnexpectedCharacters(word):
        if not wordAlreadyStored(cur, "tagalog_exception_words", word):
            pushToExceptionWordsTable(conn, cur, word, category, verbBaseForm)
    else:
        wordIsInterjectionVar = wordIsInterjection(word)
        if wordStartsWithCapitalLetter(word) and not wordIsInterjectionVar:
            category = "PN"  # Proper Noun
        elif wordIsInterjectionVar:
            category = "I"  # Interjection

        if not wordAlreadyStored(cur, "tagalog_words", word):
            wordLength, withPunctuations, alphaSortedWithoutPunctuations, \
            alphaSortedWithPunctuations, alphaSortedNoDuplicatesWithoutPunctuations, \
            alphaSortedNoDuplicatesWithPunctuations, startingsWithoutPunctuations, endingsWithoutPunctuations, \
            constituentsRowsWithoutPunctuations, startingsWithPunctuations, endingsWithPunctuations, \
            constituentsRowsWithPunctuations = getInfoFromWord(word)
            lastRowID = pushToMySQL(conn, cur, lastRowId, word, category, verbBaseForm, wordLength, withPunctuations,
                                    alphaSortedWithoutPunctuations, alphaSortedWithPunctuations,
                                    alphaSortedNoDuplicatesWithoutPunctuations, alphaSortedNoDuplicatesWithPunctuations,
                                    startingsWithoutPunctuations, endingsWithoutPunctuations,
                                    constituentsRowsWithoutPunctuations, startingsWithPunctuations,
                                    endingsWithPunctuations,
                                    constituentsRowsWithPunctuations)
            print(word)
        else:
            print(f'   --->> "{word}" not stored')

cur.close()
conn.close()
