# RPGCracker
Convert structured RPG 4  code to Free-format 

This code is meant to help anyone who needs to understand the logic flow of traditional RPG 4 code. This is done by converting the positional based RPG 4 code to the more popular free-format code. The output is a new document with the name of the code followed by “_free”
___
###Code useage:

C:\>    Python ./RPGCracker.py [yourCodehere]
___
###Ex:
C:\> dir

Mode                 LastWriteTime         Length Name
"----                 -------------         ------ ----"
"-a----         10/5/2021  10:54 AM            274 mySampleCode.rpg"

C:\> python RPGCracker.py mySampleCode.rpg
C:\> dir

Mode                 LastWriteTime         Length Name
"----                 -------------         ------ ----"
"-a----         10/5/2021  10:54 AM            274 mySampleCode.rpg"
"-a----         10/5/2021  10:14 AM            274 mySampleCode_free.rpg"
