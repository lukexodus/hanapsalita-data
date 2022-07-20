import re
import mysql.connector

conn = mysql.connector.connect(host="127.0.0.1", user="root", password="", database="hanapsalita")
cur = conn.cursor()

try:
    getLengthsSQL = "SELECT word FROM tagalog_words"
    cur.execute(getLengthsSQL)

    wordsRecords = cur.fetchall()
finally:
    cur.close()
    conn.close()

unexpectedCharsRegex = re.compile(r"[^a-zA-Z!?\-']")

for wordRecord in wordsRecords:
    word = wordRecord[0]
    if unexpectedCharsRegex.search(word) is not None:
        print(word)

