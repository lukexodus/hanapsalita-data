import json
import traceback
import datetime
import re
import sys

import lxml
import requests
from bs4 import BeautifulSoup
import mysql.connector

from scrapeUtils import pushToDatabases, wordAlreadyStored, getInfoFromWord, wordIsAmbiguous, \
    wordIsInterjection, wordStartsWithCapitalLetter, wordHasUnexpectedCharacters, \
    pushToExceptionWordsTable, processWord

searchUrl = "https://tagalog.pinoydictionary.com/list/"
startLetters = ["a", "b", "c", "d", "e", "g", "h", "i", "j", "k", "l", "m",
                "n", "o", "p", "r", "s", "t", "u", "w", "x", "y", "z"]
progressJsonFilename = "tagalog-pinoydictionary-progress.json"
wordsJsonFilename = "tagalog-pinoydictionary-words.json"
wordGroupSelector = "div.word-group"

with open(progressJsonFilename) as file:
    progressJson = json.loads(file.read())
if "lastRetrievedLetterIndex" not in progressJson:
    progressJson["lastRetrievedLetterIndex"] = 0
lastRetrievedLetterIndex = progressJson["lastRetrievedLetterIndex"]
if "lastRowId" not in progressJson:
    progressJson["lastRowId"] = None
lastRowId = progressJson["lastRowId"]

with open(wordsJsonFilename) as file:
    jsonDatabase = json.loads(file.read())
jsonDatabase.setdefault("data", {})

conn = mysql.connector.connect(host="127.0.0.1", user="root", password="", database="hanapsalita")
cur = conn.cursor()


# soup-related functions
def getPage(url):
    req = requests.get(url)
    return BeautifulSoup(req.text, "lxml")


def getNumFromLink(url):
    urlListForm = list(url)
    urlListForm.reverse()
    urlStringFormReversed = "".join(urlListForm)
    indexOfSecondToLastSlash = urlStringFormReversed.find("/", 1)
    number = url[-indexOfSecondToLastSlash:]
    return int(number.strip('/'))


def getLastPageNum(bs):
    lastPage = bs.find(title="Last Page")
    if lastPage is None:
        return None
    url = lastPage["href"]
    return getNumFromLink(url)


def getNextLetterPageInfo(startLetters, letter, searchUrl):
    if letter == startLetters[-1]:
        return None, None, None, None
    nextLetterIndex = startLetters.index(letter) + 1
    lastRetrievedLetterIndex = nextLetterIndex
    nextLetter = startLetters[nextLetterIndex]
    nextPageSoup = getPage(searchUrl + nextLetter)
    lastPageNum = getLastPageNum(nextPageSoup)

    return lastRetrievedLetterIndex, nextLetter, nextPageSoup, lastPageNum


# progressJson file-related function
def storeProgressStatusToJson(progressJson, progressJsonFilename, lastRetrievedLetterIndex, letter,
                              lastPageNum, stoppedAt, lastRowId):
    progressJson["lastRetrievedLetterIndex"] = lastRetrievedLetterIndex
    progressJson.setdefault(letter, {})
    progressJson[letter]["lastPageNum"] = lastPageNum
    progressJson[letter]["stoppedAt"] = stoppedAt
    progressJson["lastRowId"] = lastRowId
    with open(progressJsonFilename, "w") as file:
        file.write(json.dumps(progressJson))


# main function/s
def getContent(bs, progressJson, progressJsonFilename, lastRetrievedLetterIndex, letter, lastPageNum,
               stoppedAt, lastRowId):
    storeProgressStatusToJson(progressJson, progressJsonFilename, lastRetrievedLetterIndex, letter,
                              lastPageNum, stoppedAt, lastRowId)
    lastRowID = lastRowId
    searchResults = bs.select(wordGroupSelector)
    for result in searchResults:
        word = result.find("h2", class_="word-entry").get_text()
        word = word.strip()
        category = "NV"  # Non-Verb

        conjRegex = re.compile(r".*\((.*)\).*v\., inf\.", re.DOTALL)
        conjWithSubjectRegex = re.compile(r".*\((.*)\(.*v\., inf\.", re.DOTALL)
        firstWordRegex = re.compile(r"^(\w*?) ")
        hasOnlyAWordOutsideTheParenthesisRegex = re.compile(r"^(\w*) \(.*\)")
        definition = result.find("div", class_="definition").get_text()
        conjugationsRaw = conjRegex.search(definition)
        if conjugationsRaw is not None:
            category = "V"  # Verb
            verbBaseForm = word
        else:
            verbBaseForm = None

        feminineVariation, masculineVariation = wordIsAmbiguous(word)

        # if the word is a verb and has a subject or an adverb (ex. "amirulan ang labada")
        if " " in word and conjugationsRaw is not None:
            # gets only the first word or the verb
            word = firstWordRegex.search(word).group(1)
            verbBaseForm = word

            if not wordAlreadyStored(cur, "tagalog_words", word):
                lastRowID = processWord(word, conn, cur, jsonDatabase, wordsJsonFilename, lastRowID, category,
                                        verbBaseForm)

            conjugationsRaw = conjWithSubjectRegex.search(definition)
            conjugationsRawList = conjugationsRaw.group(1).split(",")
            conjugationsList = [conjugation.strip() for conjugation in conjugationsRawList]

            category = "C"  # Conjugation
            for conjugation in conjugationsList:
                if not wordAlreadyStored(cur, "tagalog_words", conjugation):
                    lastRowID = processWord(conjugation, conn, cur, jsonDatabase, wordsJsonFilename, lastRowID,
                                            category, verbBaseForm)
        elif hasOnlyAWordOutsideTheParenthesisRegex.search(word) is not None:
            word = firstWordRegex.search(word).group(1)
            if not wordAlreadyStored(cur, "tagalog_words", word):
                lastRowID = processWord(word, conn, cur, jsonDatabase, wordsJsonFilename, lastRowID, category,
                                        verbBaseForm)
        elif wordHasUnexpectedCharacters(word):
            if not wordAlreadyStored(cur, "tagalog_exception_words", word):
                pushToExceptionWordsTable(conn, cur, word, category, verbBaseForm)
        # if the word is ambiguous (ex. aktiba-bo)
        elif feminineVariation is not None:
            if not wordAlreadyStored(cur, "tagalog_words", feminineVariation):
                lastRowID = processWord(feminineVariation, conn, cur, jsonDatabase, wordsJsonFilename, lastRowID,
                                        category, verbBaseForm)
            if not wordAlreadyStored(cur, "tagalog_words", masculineVariation):
                lastRowID = processWord(masculineVariation, conn, cur, jsonDatabase, wordsJsonFilename, lastRowID,
                                        category, verbBaseForm)
        else:
            wordIsInterjectionVar = wordIsInterjection(word)
            if wordStartsWithCapitalLetter(word) and not wordIsInterjectionVar:
                category = "PN"  # Proper Noun
            elif wordIsInterjectionVar:
                category = "I"  # Interjection

            if not wordAlreadyStored(cur, "tagalog_words", word):
                lastRowID = processWord(word, conn, cur, jsonDatabase, wordsJsonFilename, lastRowID, category,
                                        verbBaseForm)

            if conjugationsRaw is not None:
                conjugationsRawList = conjugationsRaw.group(1).split(",")
                conjugationsList = [conjugation.strip() for conjugation in conjugationsRawList]

                category = "C"  # Conjugation
                for conjugation in conjugationsList:
                    if not wordAlreadyStored(cur, "tagalog_words", conjugation):
                        lastRowID = processWord(conjugation, conn, cur, jsonDatabase, wordsJsonFilename, lastRowID,
                                                category, verbBaseForm)
    return lastRowID


def getContentRecursively(searchUrl, letter, wordGroupSelector, progressJson, progressJsonFilename,
                          lastRetrievedLetterIndex, lastPageNum, lastRowId, startPageNum):
    nextPageNum = startPageNum
    succeedingPageSoup = getPage(f'{searchUrl}{letter}/{nextPageNum if nextPageNum > 1 else ""}/')
    searchResults = succeedingPageSoup.select(wordGroupSelector)
    while len(searchResults) != 0:
        nextPageNum += 1
        stoppedAt = nextPageNum - 1
        getContent(succeedingPageSoup, progressJson, progressJsonFilename, lastRetrievedLetterIndex, letter,
                   lastPageNum, stoppedAt, lastRowId)
        succeedingPageSoup = getPage(f'{searchUrl}{letter}/{nextPageNum if nextPageNum > 1 else ""}/')
        searchResults = succeedingPageSoup.select(wordGroupSelector)
    lastPageNum = nextPageNum - 1
    progressJson[letter]["lastPageNum"] = lastPageNum
    with open(progressJsonFilename, "w") as file:
        file.write(json.dumps(progressJson))


# initialize/retrieve variables to avoid letting them be undefined
letter = startLetters[lastRetrievedLetterIndex]
lastPageNum = 1
stoppedAt = 1
nextPageSoup = None

for i in range(lastRetrievedLetterIndex, len(startLetters)):
    try:
        if letter not in progressJson:  # if it's the first time to scrape the words of the specified letter
            lastPageNumRetrieved = True  # just in case the retrieval of `bs` will have an error
            if nextPageSoup is not None:
                bs = nextPageSoup
                nextPageSoup = None
            else:
                bs = getPage(searchUrl + letter)
            lastPageNumRetrieved = False

            # initialize progress information
            lastPageNum = getLastPageNum(bs)
            stoppedAt = 1

            # if the words of the specified letter are only in one to nine page/s
            # (i.e. the `Last Page` button is not found)
            if lastPageNum is None:
                lastRowId = getContent(bs, progressJson, progressJsonFilename, lastRetrievedLetterIndex, letter,
                                       lastPageNum, stoppedAt, lastRowId)
                # scrape the words until the available pages run out
                getContentRecursively(searchUrl, letter, wordGroupSelector, progressJson, progressJsonFilename,
                                      lastRetrievedLetterIndex, lastPageNum, lastRowId, 2)

                # next letter info retrieval and storing
                lastRetrievedLetterIndex, letter, nextPageSoup, lastPageNum = \
                    getNextLetterPageInfo(startLetters, letter, searchUrl)
                storeProgressStatusToJson(progressJson, progressJsonFilename, lastRetrievedLetterIndex, letter,
                                          lastPageNum, stoppedAt, lastRowId)
                continue

        else:
            lastPageNumRetrieved = True
            # retrieve progress information
            lastPageNum = progressJson[letter]["lastPageNum"]
            stoppedAt = progressJson[letter]["stoppedAt"]

            # if the words of the specified letter are only in one to nine page/s
            # (i.e. the `Last Page` button is not found)
            if lastPageNum is None:
                # scrape the words until the available pages run out
                getContentRecursively(searchUrl, letter, wordGroupSelector, progressJson, progressJsonFilename,
                                      lastRetrievedLetterIndex, lastPageNum, lastRowId, 1)

                # next letter info retrieval and storing
                stoppedAt = 1
                lastRetrievedLetterIndex, letter, nextPageSoup, lastPageNum = \
                    getNextLetterPageInfo(startLetters, letter, searchUrl)
                if letter is None:
                    break
                storeProgressStatusToJson(progressJson, progressJsonFilename, lastRetrievedLetterIndex, letter,
                                          lastPageNum, stoppedAt, lastRowId)
                continue

        startPage = stoppedAt
        for pageNum in range(startPage, lastPageNum + 1):  # continue at where the program left at the previous run
            # if the first page's soup is already retrieved then uses it for getting the words also
            if not lastPageNumRetrieved:
                bs = bs
            else:
                url = f'{searchUrl}{letter}/{pageNum if pageNum > 1 else ""}/'
                bs = getPage(url)
            lastPageNumRetrieved = True

            stoppedAt = pageNum
            lastRowId = getContent(bs, progressJson, progressJsonFilename, lastRetrievedLetterIndex, letter,
                                   lastPageNum, stoppedAt, lastRowId)

        stoppedAt = 1
        lastRetrievedLetterIndex, letter, nextPageSoup, lastPageNum = \
            getNextLetterPageInfo(startLetters, letter, searchUrl)
        storeProgressStatusToJson(progressJson, progressJsonFilename, lastRetrievedLetterIndex, letter,
                                  lastPageNum, stoppedAt, lastRowId)

    except:
        with open("tagalog-pinoydictionary-traceback.txt", "a") as file:
            file.write(f'\n{"~" * 15} {datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")} {"~" * 15}\n')
            file.write(traceback.format_exc())
        print(traceback.format_exc())
        storeProgressStatusToJson(progressJson, progressJsonFilename, lastRetrievedLetterIndex, letter, lastPageNum,
                                  stoppedAt, lastRowId)
        cur.close()
        conn.close()
        sys.exit()

storeProgressStatusToJson(progressJson, progressJsonFilename, lastRetrievedLetterIndex, letter, lastPageNum, stoppedAt,
                          lastRowId)
cur.close()
conn.close()
print('Program finished.')
