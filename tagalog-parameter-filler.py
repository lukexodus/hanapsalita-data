maxLetterNum = 60
suffix = "c_s"

with open("tagalog-parameter-filler.txt", "a") as file:
    for i in range(maxLetterNum):
        file.write(f"{i+1}{suffix} CHAR({i+1}) DEFAULT NULL,\n")
    for i in range(maxLetterNum):
        file.write(f"INDEX ({i+1}{suffix}),\n")