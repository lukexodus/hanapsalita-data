import mysql.connector

conn = mysql.connector.connect(host="127.0.0.1", user="root", password="", database="hanapsalita")
cur = conn.cursor()

words = []
with open("wordsToDelete.txt") as file:
    words = file.readlines()

try:
    for word in words:
        word = word.strip()
        cur.execute("DELETE FROM tagalog_words WHERE word=%s", (word,))
        conn.commit()
        print(word)
finally:
    cur.close()
    conn.close()


