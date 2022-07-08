listOfLists = [['s',      'u',     'c',    'e'],
               ['su',     'uc',    'cc',   'ce',  'es', 'ss'],
               ['suc',    'ucc',   'cce',  'ces', 'ess'],
               ['succ',   'ucce',  'cces', 'cess'],
               ['succe',  'ucces', 'ccess'],
               ['succes', 'uccess'],
               ['success']]


def reverseListOfLists(listOfLists):
    maxColumnNum, sublistsLengths = findMaxColumnNumAndLenOfRowSublists(listOfLists)

    # gets the length of every column
    lengthsOfColumns = []
    swappedDimensionsList = []
    for columnNum in range(maxColumnNum):
        swappedDimensionsList.append(list())
        passedACell = False
        rowNum = 0
        numberOfCellsInTheColumn = 0
        while True:
            try:
                cellValue = listOfLists[rowNum][columnNum]
                swappedDimensionsList[columnNum].append(cellValue)
                passedACell = True
                numberOfCellsInTheColumn += 1
                rowNum += 1
            except IndexError:
                if not passedACell:
                    rowNum += 1
                    continue
                else:
                    break
        lengthsOfColumns.append(numberOfCellsInTheColumn)
    return swappedDimensionsList


def findMaxColumnNumAndLenOfRowSublists(listOfLists):
    maxColumnNum = 0
    sublistsLengths = []
    for sublist in listOfLists:
        columnNum = len(sublist)
        sublistsLengths.append(columnNum)
        if columnNum > maxColumnNum:
            maxColumnNum = columnNum

    return maxColumnNum, sublistsLengths

print(reverseListOfLists(listOfLists))