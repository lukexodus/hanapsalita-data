maxLetterNum = 60

with open("tagalog-start-filler.txt", "a") as file:
    for i in range(maxLetterNum):
        file.write(f"{i+1}s CHAR({i+1}) DEFAULT NULL,\n")
    for i in range(maxLetterNum):
        file.write(f"INDEX ({i+1}s),\n")