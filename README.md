# RPGCracker
Convert structured RPG 4  code to Free-format 

This code is meant to help anyone who needs to understand the logic flow of traditional RPG 4 code. This is done by converting the positional based RPG 4 code to the more popular free-format code. The output is a new document with the name of the code followed by “_free”

Version 2: code is now object oriented to better convert programmer defined procedures

___
# Op-codes to look out for
* GOTO - GOTO op codes appear in code as a right justified structured line. This is done because the goto opcode is not suported in free-format RPG
* MOVEL - MOVEL op codes appear in code as a right justified structured line. Because MoveL can be used with strings and numbers programmer imput will be needed to decide how best to handl this instruction. This may change in the future

___
### Code useage:

**C:\\>**    Python    .\\RPGCracker.py    [yourCodehere]
___
### Example:
     C:\Rpg\> ls
      mySampleCode.rpg     RPGCracker.py

     C:\Rpg\> python .\RPGCracker.py .\mySampleCode.rpg

     . . .

     C:\Rpg\> ls
     mySampleCode.rpg      mySampleCode_free.rpg     RPGCracker.py
