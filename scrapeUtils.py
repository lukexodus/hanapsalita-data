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


"""
[odd]
purpose (7)             (chunkLen, limit)
p, u, r, p, o, s, e     (1, 7)
pu, ur, rp, po, os, se  (2, 6)
pur, urp, rpo, pos, ose (3, 5)
purp, urpo, rpos, pose  (4, 4)
purpo, urpos, rpose     (5, 3)
purpos, urpose          (6, 2)
purpose                 (7, 1)

[even]  # same process with words having an odd number of letters
enamored (8)                 (chunkLen, limit)
e, n, a, m, o, r, e, d       (1, 8)
en, na, am, mo, or, re, ed   (2, 7)
ena, nam, amo, mor, ore, red (3, 6)
enam, namo, amor, more, ored (4, 5)
enamo, namor, amore, mored   (5, 4)
enamor, namore, amored       (6, 3)
enamore, namored             (7, 2)
enamored                     (8, 1)
"""


def getConstituents(word):
    wordLength = len(word)
    constituentsColumns = []

    limit = wordLength
    # this list of lists will be in reverse dimension (i.e. (y, x) instead of (x, y))
    # since it will be inputted to a database
    for step in range(limit):
        column = []
        for chunkLen in range(1, wordLength + 1):
            constituent = word[step:step+chunkLen]
            if constituent not in column:  # remove duplicates
                column.append(constituent)
        limit -= 1
        constituentsColumns.append(column)
    return constituentsColumns


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
    """ part -> `s` (start), `e` (end), `c` (contain)"""
    parameters = ""
    for i in range(wordLength):
        parameters += f", {i+1}{part}"
    return parameters[2:]


def buildColumnParametersPlaceholders(wordLength):
    placeholders = ""
    for i in range(wordLength):
        placeholders += ", %s"
    return placeholders[2:]


# MySQL database-related functions
def wordAlreadyStored(cur, table, word):
    cur.execute("SELECT * FROM " + table + " WHERE word=%s", (word,))
    cur.fetchall()
    rowCount = cur.rowcount
    if rowCount != 0:
        return True
    return False


# main functions
def pushToMySQL(conn, cur, lastRowId, word, wordLength, category, alphaSorted, alphaSortedNoDuplicates, startings, endings, constituentsRows):
    tagalogWordsSQL = \
        "INSERT INTO tagalog_words (word, length, category, alpha_sorted, alpha_sorted_no_duplicates) VALUES (%s, %s, %s, %s, %s)"
    tagalogWordsValues = (word, wordLength, category, alphaSorted, alphaSortedNoDuplicates)
    cur.execute(tagalogWordsSQL, tagalogWordsValues)
    lastRowId1 = cur.lastrowid
    if (lastRowId is not None) and ((lastRowId + 1) != lastRowId1):
        raise Exception("`lastRowId + 1` and `lastRowId1` mismatch")
    conn.commit()

    tagalogStartSQL = \
        f"INSERT INTO tagalog_start ({buildColumnParameters(wordLength, 's')}) VALUES ({buildColumnParametersPlaceholders(wordLength)})"
    tagalogStartValues = startings
    cur.execute(tagalogStartSQL, tagalogStartValues)
    lastRowId2 = cur.lastrowid
    if lastRowId1 != lastRowId2:
        raise Exception("`lastRowId1` and `lastRowId2` mismatch")
    conn.commit()

    tagalogEndSQL = \
        f"INSERT INTO tagalog_end ({buildColumnParameters(wordLength, 'e')}) VALUES ({buildColumnParametersPlaceholders(wordLength)})"
    tagalogEndValues = endings
    cur.execute(tagalogEndSQL, tagalogEndValues)
    lastRowId3 = cur.lastrowid
    if lastRowId2 != lastRowId3:
        raise Exception("`lastRowId2` and `lastRowId3` mismatch")
    conn.commit()

    for i, constituentsRow, in enumerate(constituentsRows):
        columnLength = len(constituentsRows[i])
        tagalogContainSQL = \
            f"INSERT INTO tagalog_contain (id, {buildColumnParameters(columnLength, 'c')}) VALUES ({buildColumnParametersPlaceholders(columnLength + 1)})"

        tagalogConstituentsRowValues = [lastRowId1]
        for j, constituent in enumerate(constituentsRow):
            tagalogConstituentsRowValues.append(constituentsRow[j])
        tagalogConstituentsRowValues = tuple(tagalogConstituentsRowValues)

        cur.execute(tagalogContainSQL, tagalogConstituentsRowValues)
        lastRowId4 = cur.lastrowid
        if lastRowId3 != lastRowId4:
            raise Exception("`lastRowId3` and `lastRowId4` mismatch")
        conn.commit()

    return lastRowId1


def pushToJSON(jsonDatabase, lastRowId, word, wordLength, category, alpha_sorted, alpha_sorted_no_duplicates, startings, endings, constituentsRows):
    jsonDatabase["data"].setdefault(word, {})
    jsonDatabase["data"][word]["id"] = lastRowId
    jsonDatabase["data"][word]["length"] = wordLength
    jsonDatabase["data"][word]["category"] = category
    jsonDatabase["data"][word]["alpha_sorted"] = alpha_sorted
    jsonDatabase["data"][word]["alpha_sorted_no_duplicates"] = alpha_sorted_no_duplicates
    jsonDatabase["data"][word]["startings"] = startings
    jsonDatabase["data"][word]["endings"] = endings
    jsonDatabase["data"][word]["constituentsRows"] = constituentsRows


def pushToDatabases(conn, cur, table, jsonDatabase, lastRowId, word, wordLength, category, alphaSorted, alphaSortedNoDuplicates, startings, endings, constituentsRows):
    if not wordAlreadyStored(cur, table, word):
        lastRowID = pushToMySQL(conn, cur, lastRowId, word, wordLength, category, alphaSorted, alphaSortedNoDuplicates, startings, endings, constituentsRows)
        pushToJSON(jsonDatabase, lastRowID, word, wordLength, category, alphaSorted, alphaSortedNoDuplicates, startings,
                   endings, constituentsRows)
        print(word)
        return lastRowID
    return lastRowId