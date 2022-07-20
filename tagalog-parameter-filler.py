maxLetterNum = 60
suffix = "c_s"
tableName = "tagalog_contain_strict"

# with open("tagalog-parameter-filler.txt", "a") as file:
#     for i in range(maxLetterNum):
#         file.write(f"{i+1}{suffix} CHAR({i+1}) DEFAULT NULL,\n")
#     for i in range(maxLetterNum):
#         file.write(f"INDEX ({i+1}{suffix}),\n")


with open("tagalog-parameter-filler.txt", "a") as file:
    for i in range(13, maxLetterNum + 1):
        file.write(f"ALTER TABLE {tableName} DROP INDEX {i}{suffix};\n")
    for i in range(13, maxLetterNum + 1):
        file.write(f"ALTER TABLE {tableName} ADD INDEX({i}{suffix}(12));\n")