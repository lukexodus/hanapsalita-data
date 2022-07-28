import sys
import re
import mysql.connector

conn = mysql.connector.connect(host="127.0.0.1", port=3307, user="root", password="", database="hanapsalita")
cur = conn.cursor()

try:
    cur.execute("SELECT * FROM tagalog_words")
    wordRows = cur.fetchall()
    # conn.commit()

    # unexpectedCharsRegex = re.compile(r"[^a-zA-Z]")

    for wordRow in wordRows:
        with open("pureWords.txt", "a") as file:
            if "-" not in wordRow[1] and "'" not in wordRow[1]:
                ID = wordRow[0]
                cur.execute("DELETE FROM tagalog_start_strict WHERE id=%s", (ID,))
                conn.commit()
                cur.execute("DELETE FROM tagalog_end_strict WHERE id=%s", (ID,))
                conn.commit()
                cur.execute("DELETE FROM tagalog_contain_strict WHERE id=%s", (ID,))
                conn.commit()
                print(wordRow[0], wordRow[1])

finally:
    cur.close()
    conn.close()
