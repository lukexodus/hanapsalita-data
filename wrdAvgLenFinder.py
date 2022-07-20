import pprint

import mysql.connector

conn = mysql.connector.connect(host="127.0.0.1", user="root", password="", database="hanapsalita")
cur = conn.cursor()

try:
    getLengthsSQL = "SELECT length FROM tagalog_words"
    cur.execute(getLengthsSQL)

    lengths = cur.fetchall()
finally:
    cur.close()
    conn.close()

wordsTotal = 78450
wordLettersTotal = 0
wordsWithLengthStats = {}

for lengthTuple in lengths:
    length = lengthTuple[0]
    if length in wordsWithLengthStats:
        wordsWithLengthStats[length] += 1
    else:
        wordsWithLengthStats.setdefault(length, 1)
    wordLettersTotal += length

avg = wordLettersTotal / wordsTotal

with open("wrdAvgLen.txt", "a") as file:
    file.write(f"""Words total: {wordsTotal}
Word letters total: {wordLettersTotal}
Word length average: {avg}
Word with lengths counts statistics: {pprint.pformat(wordsWithLengthStats)}""")
