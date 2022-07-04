import json
import traceback
import datetime
import re
import sys

import lxml
import requests
from bs4 import BeautifulSoup
import mysql.connector

from scrapeUtils import getStartings, getEndings, getConstituents, sortAlphabetically, pushToDatabases,\
    wordAlreadyStored, getInfoFromWord

searchUrl = "https://tagalog.pinoydictionary.com/list/"
startLetters = ["a", "b", "c", "d", "e", "g", "h", "i", "j", "k", "l", "m",
                "n", "o", "p", "r", "s", "t", "u", "w", "x", "y", "z"]
progressJsonFilename = "tagalog-pinoydictionary-progress.json"
wordsJsonFilename = "tagalog-pinoydictionary-words.json"

with open(progressJsonFilename) as file:
    progressJson = json.loads(file.read())
if "lastRetrievedLetterIndex" not in progressJson:
    progressJson["lastRetrievedLetterIndex"] = 0
lastRetrievedLetterIndex = progressJson["lastRetrievedLetterIndex"]
if "lastRowId" not in progressJson:
    progressJson["lastRowId"] = None
lastRowId = progressJson["lastRowId"]

with open("tagalog-pinoydictionary-words.json") as file:
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
    if lastPage == None:
        return None
    url = lastPage["href"]
    return getNumFromLink(url)


def getNextLetterPageInfo(startLetters, letter, searchUrl):
    nextLetterIndex = startLetters.index(letter) + 1
    lastRetrievedLetterIndex = nextLetterIndex
    nextLetter = startLetters[nextLetterIndex]
    nextPageSoup = getPage(searchUrl + letter)
    lastPageNum = getLastPageNum(nextPageSoup)
    if lastPageNum is None:
        lastPageNum = 1

    return lastRetrievedLetterIndex, nextLetter, nextPageSoup, lastPageNum


# progressJson file-related function
def storeProgressStatusToJson(progressJson, progressJsonFilename, lastRetrievedLetterIndex, letter, lastPageNum, stoppedAt, lastRowId):
    progressJson["lastRetrievedLetterIndex"] = lastRetrievedLetterIndex
    progressJson.setdefault(letter, {})
    progressJson[letter]["lastPageNum"] = lastPageNum
    progressJson[letter]["stoppedAt"] = stoppedAt
    progressJson["lastRowId"] = lastRowId
    with open(progressJsonFilename, "w") as file:
        file.write(json.dumps(progressJson))


# main function
def getContent(bs, lastRowId):
    searchResults = bs.select("div.word-group")
    for result in searchResults: # Not Conjugation
        word = result.find("h2", class_="word-entry").get_text()

        if " " in word:
            continue
        else:
            conjRegex = re.compile(r".*\((.*)\).*v\., inf\.", re.DOTALL)
            definition = result.find("div", class_="definition").get_text()
            conjugationsRaw = conjRegex.search(definition)

            category = "NC"
            if not wordAlreadyStored(cur, "tagalog_words", word):
                wordInfo = getInfoFromWord(word)
                variablesToBePushed = [conn, cur, jsonDatabase, wordsJsonFilename, lastRowId, word, category]
                variablesToBePushed.extend(wordInfo)
                lastRowId = pushToDatabases(*variablesToBePushed)
            if conjugationsRaw is not None:
                conjugationsRawList = conjugationsRaw.group(1).split(",")
                conjugationsList = [conjugation.strip() for conjugation in conjugationsRawList]

                category = "C"  # Conjugation
                for conjugation in conjugationsList:
                    if not wordAlreadyStored(cur, "tagalog_words", conjugation):
                        wordInfo = getInfoFromWord(conjugation)
                        variablesToBePushed = [conn, cur, jsonDatabase, wordsJsonFilename, lastRowId, conjugation,
                                               category]
                        variablesToBePushed.extend(wordInfo)
                        lastRowId = pushToDatabases(*variablesToBePushed)
    return lastRowId


# initialize/retrieve variables to avoid letting them be undefined
letter = startLetters[lastRetrievedLetterIndex]
lastPageNum = 1
stoppedAt = 1
nextPageSoup = None

for i in range(lastRetrievedLetterIndex, len(startLetters)):
    try:
        if letter not in progressJson:  # if it's the first time to scrape the words of the specified letter
            lastPageNumRetrieved = False

            if nextPageSoup is not None:
                bs = nextPageSoup
                nextPageSoup = None
            else:
                bs = getPage(searchUrl + letter)

            lastPageNum = getLastPageNum(bs)
            stoppedAt = 1
            if lastPageNum is None:  # if the words of the specified letter are only in one page
                lastRowId = getContent(bs, lastRowId)
                # prepares to jump at the next letter
                progressJson[letter]["stoppedAt"] = stoppedAt
                lastRetrievedLetterIndex, letter, nextPageSoup, lastPageNum = \
                    getNextLetterPageInfo(startLetters, letter, searchUrl)
                storeProgressStatusToJson(progressJson, progressJsonFilename, lastRetrievedLetterIndex, letter, lastPageNum, stoppedAt,
                                          lastRowId)
                continue

        else:  # retrieve progress information
            lastPageNumRetrieved = True
            lastPageNum = progressJson[letter]["lastPageNum"]
            stoppedAt = progressJson[letter]["stoppedAt"]

        for pageNum in range(stoppedAt, lastPageNum + 1):  # continue at where the program left at the previous run
            if not lastPageNumRetrieved:  # if `bs` is already retrieved or not (i.e. defined or not)
                bs = bs
            else:
                url = f'{searchUrl}{letter}/{pageNum if pageNum > 1 else ""}/'
                bs = getPage(url)
            lastRowId = getContent(bs, lastRowId)

            if stoppedAt == lastPageNum:  # if arrived at the last page
                # prepares to jump at the next letter
                progressJson[letter]["stoppedAt"] = stoppedAt
                lastRetrievedLetterIndex, letter, nextPageSoup, lastPageNum = \
                    getNextLetterPageInfo(startLetters, letter, searchUrl)

            else:
                stoppedAt += 1
            storeProgressStatusToJson(progressJson, progressJsonFilename, lastRetrievedLetterIndex, letter, lastPageNum, stoppedAt, lastRowId)
    except:
        with open("tagalog-pinoydictionary-traceback.txt", "a") as file:
            file.write(f'\n{"~" * 15} {datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")} {"~" * 15}\n')
            file.write(traceback.format_exc())
        print(traceback.format_exc())
    finally:
        storeProgressStatusToJson(progressJson, progressJsonFilename, lastRetrievedLetterIndex, letter, lastPageNum, stoppedAt, lastRowId)
        sys.exit()

storeProgressStatusToJson(progressJson, progressJsonFilename, lastRetrievedLetterIndex, letter, lastPageNum, stoppedAt, lastRowId)
print('Program finished.')
