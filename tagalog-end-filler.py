maxLetterNum = 60

with open("tagalog-end-filler.txt", "a") as file:
    for i in range(maxLetterNum):
        file.write(f"{i+1}e CHAR({i+1}) DEFAULT NULL,\n")
    for i in range(maxLetterNum):
        file.write(f"INDEX ({i+1}e),\n")