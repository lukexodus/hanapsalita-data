# string functions
def getStartings(word):
    startings = []
    for i in range(len(word)):
        startings.append(word[:i+1])
    return tuple(startings)


def getEndings(word):
    endings = []
    for i in range(len(word) -1, -1, -1):
        endings.append(word[i:len(word)])
    return tuple(endings)


def sortAlphabetically(word):
    wordList = list(word)
    wordList.sort()
    alphaSorted = "".join(wordList)
    alphaSortedNoDuplicates = ""
    i = 0
    while wordList:
        if wordList[0] not in alphaSortedNoDuplicates:
            alphaSortedNoDuplicates += wordList[0]
        wordList.pop(0)
    return alphaSorted, alphaSortedNoDuplicates


# SQL queries-related functions
def buildColumnParameters(wordLength, part):
    """ part -> `s` (start) or `e` (end)"""
    parameters = ""
    for i in range(wordLength):
        parameters += f", {i+1}{part}"
    return parameters[2:]


def buildColumnParametersPlaceholders(wordLength):
    placeholders = ""
    for i in range(wordLength):
        placeholders += ", %s"
    return placeholders[2:]


# database-related functions
def wordAlreadyStored(cur, table, word):
    cur.execute("SELECT * FROM %s WHERE word=%s", (table, word))
    cur.fetchall()
    rowCount = cur.rowcount
    if rowCount != 0:
        return True
    return False


# main functions
def pushToMySQL(conn, cur, word, category, alphaSorted, alphaSortedNoDuplicates, startings, endings):
    wordLength = len(word)

    tagalogWordsSQL = \
        f"INSERT INTO tagalog_words (word, length, category, alpha_sorted, alpha_sorted_no_duplicates) VALUES (%s, %s, %s, %s, %s)"
    tagalogWordsValues = (word, wordLength, category, alphaSorted, alphaSortedNoDuplicates)
    cur.execute(tagalogWordsSQL, tagalogWordsValues)
    conn.commit()

    tagalogStartSQL = \
        f"INSERT INTO tagalog_start ({buildColumnParameters(wordLength, 's')}) VALUES ({buildColumnParametersPlaceholders(wordLength)})"
    tagalogStartValues = startings
    cur.execute(tagalogStartSQL, tagalogStartValues)
    conn.commit()

    tagalogEndSQL = \
        f"INSERT INTO tagalog_end ({buildColumnParameters(wordLength, 'e')}) VALUES ({buildColumnParametersPlaceholders(wordLength)})"
    tagalogEndValues = endings
    cur.execute(tagalogEndSQL, tagalogEndValues)
    conn.commit()
