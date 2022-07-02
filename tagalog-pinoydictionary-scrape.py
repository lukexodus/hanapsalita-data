import json
import traceback
import datetime
import re
import sys

import lxml
import requests
from bs4 import BeautifulSoup
import mysql.connector

from scrapeUtils import getStartings, getEndings, sortAlphabetically, wordAlreadyStored, pushToMySQL

searchUrl = "https://tagalog.pinoydictionary.com/list/"
startLetters = ["a", "b", "c", "d", "e", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u", "w", "x", "y", "z"]

with open("tagalog-pinoydictionary-progress.json") as file:
    progressJson = json.loads(file.read())
if "lastRetrievedLetter" not in progressJson:
    progressJson["lastRetrievedLetter"] = 0
lastRetrievedLetter = progressJson["lastRetrievedLetter"]

with open("tagalog-pinoydictionary-words.json") as file:
    data = json.loads(file.read())
data.setdefault("data", {})

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


def getContent(bs):
    conjRegex = re.compile(r".*\((.*)\).*v\., inf\.", re.DOTALL)
    searchResults = bs.select("div.word-group")
    for result in searchResults:
        category = "NC"  # Not Conjugation
        word = result.find("h2", class_="word-entry").get_text()
        if " " in word:
            continue
        else:
            alphaSorted, alphaSortedNoDuplicates = sortAlphabetically(word)
            startings, endings = getStartings(word), getEndings(word)

            definition = result.find("div", class_="definition").get_text()
            conjugationsRaw = conjRegex.search(definition)
            if conjugationsRaw is not None:
                conjugationsRawList = conjugationsRaw.group(1).split(",")
                conjugationsList = [conjugation.strip() for conjugation in conjugationsRawList]
                if not wordAlreadyStored(cur, "tagalog_words", word):
                    pushToMySQL(conn, cur, word, category, alphaSorted, alphaSortedNoDuplicates, startings, endings)
                    print(word)

                category = "C"  # Conjugation
                for conjugation in conjugationsList:
                    alphaSorted, alphaSortedNoDuplicates = sortAlphabetically(conjugation)
                    startings, endings = getStartings(conjugation), getEndings(conjugation)
                    if not wordAlreadyStored(cur, "tagalog_words", conjugation):
                        pushToMySQL(conn, cur, word, category, alphaSorted, alphaSortedNoDuplicates, startings, endings)
                        print(conjugation)

            else:
                if not wordAlreadyStored(cur, "tagalog_words", word):
                    pushToMySQL(conn, cur, word, category, alphaSorted, alphaSortedNoDuplicates, startings, endings)
                    print(word)


nextPageSoup = None
for i in range(lastRetrievedLetter, len(startLetters)):
    try:
        letter = startLetters[lastRetrievedLetter]
        if letter not in progressJson:
            lastPageNumRetrieved = False
            if nextPageSoup is not None:
                bs = nextPageSoup
                nextPageSoup = None
            else:
                bs = getPage(searchUrl + letter)
            lastPageNum = getLastPageNum(bs)
            stoppedAt = 1
            if lastPageNum is None:
                getContent(bs)
                # ----- Duplicate
                progressJson[letter]["stoppedAt"] = stoppedAt
                nextLetterIndex = startLetters.index(letter) + 1
                lastRetrievedLetter = nextLetterIndex
                letter = startLetters[nextLetterIndex]
                stoppedAt = 1
                nextPageSoup = getPage(searchUrl + letter)
                lastPageNum = getLastPageNum(nextPageSoup)
                # -----
                if lastPageNum is None:
                    lastPageNum = 1
                continue
        else:
            lastPageNumRetrieved = True
            lastPageNum = progressJson[letter]["lastPage"]
            stoppedAt = progressJson[letter]["stoppedAt"]
        for pageNum in range(stoppedAt, lastPageNum + 1):
            if not lastPageNumRetrieved:
                bs = bs
                lastPageNumRetrieved = True
            else:
                url = f'{searchUrl}{letter}/{pageNum if pageNum > 1 else ""}/'
                bs = getPage(url)
            getContent(bs)
            if stoppedAt == lastPageNum:
                # ----- Duplicate
                progressJson[letter]["stoppedAt"] = stoppedAt
                nextLetterIndex = startLetters.index(letter) + 1
                lastRetrievedLetter = nextLetterIndex
                letter = startLetters[nextLetterIndex]
                stoppedAt = 1
                nextPageSoup = getPage(searchUrl + letter)
                lastPageNum = getLastPageNum(nextPageSoup)
                # -----
                if lastPageNum is None:
                    lastPageNum = 1
            else:
                stoppedAt += 1
    except:
        with open("tagalog-pinoydictionary-traceback.txt", "a") as file:
            file.write(f'\n{"~" * 15} {datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")} {"~" * 15}\n')
            file.write(traceback.format_exc())
        print(traceback.format_exc())
    finally:
        progressJson["lastRetrievedLetter"] = lastRetrievedLetter
        progressJson.setdefault(letter, {})
        progressJson[letter]["lastPage"] = lastPageNum
        progressJson[letter]["stoppedAt"] = stoppedAt
        with open("tagalog-pinoydictionary-progress.json", "w") as file:
            file.write(json.dumps(progressJson))
        sys.exit()