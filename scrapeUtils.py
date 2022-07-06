import json
import re

# string functions
def getStartings(word):
    startingsWithoutPunctuations = []
    for i in range(len(word)):
        startingsWithoutPunctuations.append(word[:i+1])
    return startingsWithoutPunctuations


def getEndings(word):
    endingsWithoutPunctuations = []
    for i in range(len(word) -1, -1, -1):
        endingsWithoutPunctuations.append(word[i:len(word)])
    return endingsWithoutPunctuations


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
    alphaSortedNoDuplicates = []
    i = 0
    while wordList:
        if wordList[0] not in alphaSortedNoDuplicates:
            alphaSortedNoDuplicates += wordList[0]
        wordList.pop(0)
    alphaSortedNoDuplicates = "".join(alphaSortedNoDuplicates)
    return alphaSorted, alphaSortedNoDuplicates


def wordIsAmbiguous(word):  # ambiguous words are those that can be feminine or masculine (ex. akitba-bo)
    ambiguousWordRegex = re.compile(r"^((\w+)(\w)a-(\w)o)$")
    ambiguousWordMO = ambiguousWordRegex.search(word)
    if ambiguousWordMO is None:
        return None, None
    firstPart = ambiguousWordMO.group(2)
    secondToTheLastLetter1 = ambiguousWordMO.group(3)
    secondToTheLastLetter2 = ambiguousWordMO.group(4)
    if secondToTheLastLetter1 != secondToTheLastLetter2:
        return None, None
    return firstPart + secondToTheLastLetter1 + "a", firstPart + secondToTheLastLetter2 + "o"


def wordIsInterjection(word):
    endsWithExclamationOrQuestionMark = re.compile(r"[!?]$")
    mark = endsWithExclamationOrQuestionMark.search(word)
    if mark is not None:
        return True
    return False


def wordStartsWithCapitalLetter(word):
    startsWithCapitalLetterRegex = re.compile(r"^[A-Z]")
    capitalLetter = startsWithCapitalLetterRegex.search(word)
    if capitalLetter is not None:
        return True
    return False


def wordHasUnexpectedCharacters(word):
    unexpectedCharactersRegex = re.compile(r"[^A-Za-z!?'-]")
    unexpectedCharacters = unexpectedCharactersRegex.search(word)
    if unexpectedCharacters is not None:
        return True
    return False


def purifyWord(word):
    """Removed all non-word characters"""
    nonWordRegex = re.compile(r"\W")
    wordPurified = nonWordRegex.sub("", word)
    return wordPurified


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
def pushToMySQL(conn, cur, lastRowId, word, category, verbBaseForm, wordLength, withPunctuations,
                alphaSortedWithoutPunctuations, alphaSortedWithPunctuations, alphaSortedNoDuplicatesWithoutPunctuations,
                alphaSortedNoDuplicatesWithPunctuations, startingsWithoutPunctuations, endingsWithoutPunctuations,
                constituentsRowsWithoutPunctuations, startingsWithPunctuations, endingsWithPunctuations,
                constituentsRowsWithPunctuations):
    if not withPunctuations and verbBaseForm is not None:
        tagalogWordsValues = (word, wordLength, category, verbBaseForm, alphaSortedWithPunctuations,
                              alphaSortedNoDuplicatesWithPunctuations)
        tagalogWordsSQL = \
            f"INSERT INTO tagalog_words (word, length, category, verb_base_form, alpha_sorted_not_strict, alpha_sorted_no_duplicates_not_strict) VALUES ({buildColumnParametersPlaceholders(len(tagalogWordsValues))})"
    elif withPunctuations and verbBaseForm is not None:
        tagalogWordsValues = (word, wordLength, category, verbBaseForm, alphaSortedWithoutPunctuations,
                              alphaSortedWithPunctuations, alphaSortedNoDuplicatesWithoutPunctuations,
                              alphaSortedNoDuplicatesWithPunctuations)
        tagalogWordsSQL = \
            f"INSERT INTO tagalog_words (word, length, category, verb_base_form, alpha_sorted_not_strict, alpha_sorted_strict, alpha_sorted_no_duplicates_not_strict, alpha_sorted_no_duplicates_strict) VALUES ({buildColumnParametersPlaceholders(len(tagalogWordsValues))})"
    elif not withPunctuations and verbBaseForm is None:
        tagalogWordsValues = (word, wordLength, category, alphaSortedWithPunctuations,
                              alphaSortedNoDuplicatesWithPunctuations)
        tagalogWordsSQL = \
            f"INSERT INTO tagalog_words (word, length, category, alpha_sorted_not_strict, alpha_sorted_no_duplicates_not_strict) VALUES ({buildColumnParametersPlaceholders(len(tagalogWordsValues))})"
    elif withPunctuations and verbBaseForm is None:
        tagalogWordsValues = (word, wordLength, category, alphaSortedWithoutPunctuations,
                              alphaSortedWithPunctuations, alphaSortedNoDuplicatesWithoutPunctuations,
                              alphaSortedNoDuplicatesWithPunctuations)
        tagalogWordsSQL = \
            f"INSERT INTO tagalog_words (word, length, category, alpha_sorted_not_strict, alpha_sorted_strict, alpha_sorted_no_duplicates_not_strict, alpha_sorted_no_duplicates_strict) VALUES ({buildColumnParametersPlaceholders(len(tagalogWordsValues))})"
    cur.execute(tagalogWordsSQL, tagalogWordsValues)
    lastRowId1 = cur.lastrowid
    # if (lastRowId is not None) and ((lastRowId + 1) != lastRowId1):
    #     raise Exception("`lastRowId + 1` and `lastRowId1` mismatch")
    conn.commit()

    # tagalog_start_*
    tagalogStartNotStrictValues = [lastRowId1] + startingsWithoutPunctuations
    tagalogStartNotStrictSQL = \
        f"INSERT INTO tagalog_start_not_strict (id, {buildColumnParameters(len(tagalogStartNotStrictValues) - 1, 's_ns')}) VALUES ({buildColumnParametersPlaceholders(len(tagalogStartNotStrictValues))})"
    cur.execute(tagalogStartNotStrictSQL, tagalogStartNotStrictValues)
    conn.commit()

    tagalogStartStrictValues = [lastRowId1] + startingsWithPunctuations
    tagalogStartStrictSQL = \
        f"INSERT INTO tagalog_start_strict (id, {buildColumnParameters(len(tagalogStartStrictValues) - 1, 's_s')}) VALUES ({buildColumnParametersPlaceholders(len(tagalogStartStrictValues))})"
    cur.execute(tagalogStartStrictSQL, tagalogStartStrictValues)
    conn.commit()

    # tagalog_end_*
    tagalogEndNotStrictValues = [lastRowId1] + endingsWithoutPunctuations
    tagalogEndNotStrictSQL = \
        f"INSERT INTO tagalog_end_not_strict (id, {buildColumnParameters(len(tagalogEndNotStrictValues) - 1, 'e_ns')}) VALUES ({buildColumnParametersPlaceholders(len(tagalogEndNotStrictValues))})"
    cur.execute(tagalogEndNotStrictSQL, tagalogEndNotStrictValues)
    conn.commit()

    tagalogEndStrictValues = [lastRowId1] + endingsWithPunctuations
    tagalogEndStrictSQL = \
        f"INSERT INTO tagalog_end_strict (id, {buildColumnParameters(len(tagalogEndStrictValues) - 1, 'e_s')}) VALUES ({buildColumnParametersPlaceholders(len(tagalogEndStrictValues))})"
    cur.execute(tagalogEndStrictSQL, tagalogEndStrictValues)
    conn.commit()

    # tagalog_contain_*
    for i, constituentsRow, in enumerate(constituentsRowsWithoutPunctuations):
        columnLength = len(constituentsRowsWithoutPunctuations[i])
        tagalogContainNotStrictSQL = \
            f"INSERT INTO tagalog_contain_not_strict (id, {buildColumnParameters(columnLength, 'c_ns')}) VALUES ({buildColumnParametersPlaceholders(columnLength + 1)})"

        tagalogConstituentsRowValuesNotStrict = [lastRowId1]
        for j, constituent in enumerate(constituentsRow):
            tagalogConstituentsRowValuesNotStrict.append(constituentsRow[j])
        tagalogConstituentsRowValuesNotStrict = tuple(tagalogConstituentsRowValuesNotStrict)

        cur.execute(tagalogContainNotStrictSQL, tagalogConstituentsRowValuesNotStrict)
        conn.commit()

    for i, constituentsRow, in enumerate(constituentsRowsWithPunctuations):
        columnLength = len(constituentsRowsWithPunctuations[i])
        tagalogContainStrictSQL = \
            f"INSERT INTO tagalog_contain_strict (id, {buildColumnParameters(columnLength, 'c_s')}) VALUES ({buildColumnParametersPlaceholders(columnLength + 1)})"

        tagalogConstituentsRowValuesStrict = [lastRowId1]
        for j, constituent in enumerate(constituentsRow):
            tagalogConstituentsRowValuesStrict.append(constituentsRow[j])
        tagalogConstituentsRowValuesStrict = tuple(tagalogConstituentsRowValuesStrict)

        cur.execute(tagalogContainStrictSQL, tagalogConstituentsRowValuesStrict)
        conn.commit()

    return lastRowId1


def pushToJSON(jsonDatabase, wordsJsonFilename, lastRowId, word, category, verbBaseForm, wordLength, withPunctuations,
               alphaSortedWithoutPunctuations, alphaSortedWithPunctuations, alphaSortedNoDuplicatesWithoutPunctuations,
               alphaSortedNoDuplicatesWithPunctuations, startingsWithoutPunctuations, endingsWithoutPunctuations,
               constituentsRowsWithoutPunctuations, startingsWithPunctuations, endingsWithPunctuations,
               constituentsRowsWithPunctuations):
    jsonDatabase["lastRowId"] = lastRowId
    jsonDatabase["data"].setdefault(word, {})
    jsonDatabase["data"][word]["id"] = lastRowId
    jsonDatabase["data"][word]["length"] = wordLength
    jsonDatabase["data"][word]["category"] = category
    jsonDatabase["data"][word]["verb_base_form"] = verbBaseForm
    jsonDatabase["data"][word]["withPunctuations"] = withPunctuations
    jsonDatabase["data"][word]["alpha_sorted_not_strict"] = alphaSortedWithoutPunctuations
    jsonDatabase["data"][word]["alpha_sorted_strict"] = alphaSortedWithPunctuations
    jsonDatabase["data"][word]["alpha_sorted_no_duplicates_not_strict"] = alphaSortedNoDuplicatesWithoutPunctuations
    jsonDatabase["data"][word]["alpha_sorted_no_duplicates_strict"] = alphaSortedNoDuplicatesWithPunctuations
    jsonDatabase["data"][word]["startings_not_strict"] = startingsWithoutPunctuations
    jsonDatabase["data"][word]["endings_not_strict"] = endingsWithoutPunctuations
    jsonDatabase["data"][word]["contain_not_strict"] = constituentsRowsWithoutPunctuations
    jsonDatabase["data"][word]["startings_strict"] = startingsWithPunctuations
    jsonDatabase["data"][word]["endings_strict"] = endingsWithPunctuations
    jsonDatabase["data"][word]["contain_strict"] = constituentsRowsWithPunctuations

    with open(wordsJsonFilename, "w") as file:
        file.write(json.dumps(jsonDatabase))


def pushToExceptionWordsTable(conn, cur, word, category, verbBaseForm):
    if verbBaseForm is None:
        tagalogExceptionWordsValues = (word, category)
        tagalogExceptionWordsSQL = \
            f"INSERT INTO tagalog_exception_words (word, category) VALUES ({buildColumnParametersPlaceholders(len(tagalogExceptionWordsValues))})"
    else:
        tagalogExceptionWordsValues = (word, category, verbBaseForm)
        tagalogExceptionWordsSQL = \
            f"INSERT INTO tagalog_exception_words (word, category, verb_base_form) VALUES ({buildColumnParametersPlaceholders(len(tagalogExceptionWordsValues))})"
        cur.execute(tagalogExceptionWordsValues, tagalogExceptionWordsSQL)
        conn.commit()


def pushToDatabases(conn, cur, jsonDatabase, wordsJsonFilename, lastRowId, word, category, verbBaseForm,  wordLength,
                    withPunctuations, alphaSortedWithoutPunctuations, alphaSortedWithPunctuations,
                    alphaSortedNoDuplicatesWithoutPunctuations, alphaSortedNoDuplicatesWithPunctuations,
                    startingsWithoutPunctuations, endingsWithoutPunctuations, constituentsRowsWithoutPunctuations,
                    startingsWithPunctuations, endingsWithPunctuations, constituentsRowsWithPunctuations):
    lastRowID = pushToMySQL(conn, cur, lastRowId, word, category, verbBaseForm, wordLength, withPunctuations,
                            alphaSortedWithoutPunctuations, alphaSortedWithPunctuations,
                            alphaSortedNoDuplicatesWithoutPunctuations, alphaSortedNoDuplicatesWithPunctuations,
                            startingsWithoutPunctuations, endingsWithoutPunctuations,
                            constituentsRowsWithoutPunctuations, startingsWithPunctuations, endingsWithPunctuations,
                            constituentsRowsWithPunctuations)
    pushToJSON(jsonDatabase, wordsJsonFilename, lastRowID, word, category, verbBaseForm, wordLength, withPunctuations,
               alphaSortedWithoutPunctuations, alphaSortedWithPunctuations, alphaSortedNoDuplicatesWithoutPunctuations,
               alphaSortedNoDuplicatesWithPunctuations, startingsWithoutPunctuations, endingsWithoutPunctuations,
               constituentsRowsWithoutPunctuations, startingsWithPunctuations, endingsWithPunctuations,
               constituentsRowsWithPunctuations)
    print(word)
    return lastRowID


punctuations = "!?'-,"


def getInfoFromWord(word):
    wordStrippedAndLowered = word.strip(punctuations).lower()  # for the *_strict tables
    wordPurified = purifyWord(wordStrippedAndLowered)  # for the *_not_strict tables
    wordLength = len(wordPurified)
    withPunctuations = True if ("-" in wordStrippedAndLowered) or ("'" in wordStrippedAndLowered) else False

    alphaSortedWithPunctuations, alphaSortedNoDuplicatesWithPunctuations = sortAlphabetically(wordStrippedAndLowered)
    alphaSortedWithoutPunctuations, alphaSortedNoDuplicatesWithoutPunctuations = sortAlphabetically(wordPurified)

    startingsWithoutPunctuations, endingsWithoutPunctuations = getStartings(wordPurified), getEndings(wordPurified)
    constituentsRowsWithoutPunctuations = getConstituents(wordPurified)

    startingsWithPunctuations, endingsWithPunctuations = getStartings(wordStrippedAndLowered), getEndings(wordStrippedAndLowered)
    constituentsRowsWithPunctuations = getConstituents(wordStrippedAndLowered)

    return wordLength, withPunctuations, alphaSortedWithoutPunctuations, alphaSortedWithPunctuations,\
        alphaSortedNoDuplicatesWithoutPunctuations, alphaSortedNoDuplicatesWithPunctuations, \
        startingsWithoutPunctuations, endingsWithoutPunctuations, constituentsRowsWithoutPunctuations, \
        startingsWithPunctuations, endingsWithPunctuations, constituentsRowsWithPunctuations


def processWord(word, conn, cur, jsonDatabase, wordsJsonFilename, lastRowId, category, verbBaseForm):
    """Wrapper function for `getInfoFromWord` and `pushToDatabases`"""
    wordInfo = getInfoFromWord(word)
    variablesToBePushed = [conn, cur, jsonDatabase, wordsJsonFilename, lastRowId, word, category, verbBaseForm]
    variablesToBePushed.extend(wordInfo)
    lastRowID = pushToDatabases(*variablesToBePushed)
    return lastRowID
