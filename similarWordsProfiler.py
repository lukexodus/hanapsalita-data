import pprint
import mysql.connector

conn = mysql.connector.connect(host="127.0.0.1", user="root", password="", database="hanapsalita")
cur = conn.cursor()

try:
    cur.execute("SELECT word,length FROM tagalog_words ORDER BY length")
    wordsTuples = cur.fetchall()
finally:
    cur.close()
    conn.close()

similarWordsProfile = {}
initialLength = 0
lengthStep = initialLength
previousWordChunk = ""

for wordTuple in wordsTuples:
    word, length = wordTuple[0], wordTuple[1]
    if length != lengthStep:
        similarWordsProfile.setdefault(length, 0)
    wordChunk = word[:-1]
    if wordChunk == previousWordChunk:
        similarWordsProfile[length] += 1
    previousWordChunk = wordChunk

with open("similarWordsProfile.txt", "a") as file:
    file.write(pprint.pformat(similarWordsProfile))