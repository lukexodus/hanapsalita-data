import re
from bs4 import BeautifulSoup

wordGroupSelector = "div.word-group"

file = open("wordgroup.html")

endsWithClosingParenthesisRegex = re.compile(r"\)$")

conjRegex = re.compile(r".*\((.*)\).*v\., inf\.", re.DOTALL)
conjWithSubjectRegex = re.compile(r".*\((.*)\(.*v\., inf\.", re.DOTALL)
firstWordRegex = re.compile(r"^(\w*?) ")
hasOnlyAWordOutsideTheParenthesisRegex = re.compile(r"^(\w*) \(.*\)")

bs = BeautifulSoup(file.read(), "html.parser")
searchResults = bs.select(wordGroupSelector)
for result in searchResults:
    word = result.find("h2", class_="word-entry").get_text()

    definition = result.find("div", class_="definition").get_text()
    conjugationsRaw = conjRegex.search(definition)
    print(conjugationsRaw.group())
    print(conjugationsRaw.group(1))


file.close()
