import sys
import platform

gblFileDivision = ""
gblDataDivision = ""
gblProcedureDivision = ""
gblTmp = ""
gblParams = {"": []}
gblKeys = {"":[]}
gblInLineDeclare = []
gblIndent = ""
gblProgramName = ""
gblSQLBlock = {"": ""}
gblMVRStr = ""

def clearFile(path):
    f = open(path, 'w')
    f.write("")
    f.close()

# /////////////////////////////////////////////////////////////////////////
def write(path, data):
    f = open(path, 'a')
    f.write(data)
    f.close()

# /////////////////////////////////////////////////////////////////////////
def read(path):
    # Open the file with read only permit
    f = open(path, "r")

    # use readlines to read all lines in the file
    # The variable "lines" is a list containing all lines in the file
    lines = f.readlines()

    # close the file after reading the lines.
    f.close()

    return lines

# /////////////////////////////////////////////////////////////////////////
def addSQLBlock(keyName, value):
    global gblSQLBlock

    if keyName in gblSQLBlock:
        if value == ";":
            gblSQLBlock[keyName] += value + "\n"
        else:
            gblSQLBlock[keyName] += "\n" + value
    else:
        gblSQLBlock[keyName] = value

# /////////////////////////////////////////////////////////////////////////
def addCallParamList(keyName, value):
    global gblParams

    if keyName in gblParams:
        gblParams[keyName].append(value)
    else:
        gblParams[keyName] = [value]

# /////////////////////////////////////////////////////////////////////////
def getExternalProcCall(procName):
    name = procName.replace("'","")

    lst = getCallParamList(name)

    return "{0}{1};".format(name, lst)

# /////////////////////////////////////////////////////////////////////////
def addkeyList(keyName, value):
    global gblKeys

    if keyName in gblKeys:
        gblKeys[keyName].append(value)
    else:
        gblKeys[keyName] = [value]

# /////////////////////////////////////////////////////////////////////////
def getKeyString(keyName):
    global gblKeys
    ret = ""

    if keyName in gblKeys:
        arr = gblKeys[keyName]

        for i in range(len(arr)):
            if i > 0:
                if i < (len(arr) - 1):
                    ret += arr[i] + ": "
                else:
                    ret += arr[i]
        return "(" + ret + ")"
    
    return "(" + keyName + ")"
    
# /////////////////////////////////////////////////////////////////////////
def getRPG3_ComparisonOp(op):
    drez = {"EQ":"=", "NE":"<>","LT":"<","LE":"<=","GT":">","GE":">="}
    operand = op[len(op)-2:]

    return drez[operand]

# /////////////////////////////////////////////////////////////////////////
def getCallParamList(callName):
    global gblParams
    ret = ""

    # check if call is in paramiter dicationary
    if callName in gblParams:
        arr = gblKeys[callName]

        # format the list retreived from the dictionary
        # and format the string for the call
        for i in range(len(arr)):
            if i > 0:
                if i < (len(arr) - 1):
                    ret += arr[i] + ": "
                else:
                    ret += arr[i]
        return "(" + ret + ")"
    
    return "()"

# /////////////////////////////////////////////////////////////////////////
def translateIndicators(hi, lo, eq):
    key = ""
    res = ""
    op = ""

    # get result and build key string
    # key is used to find operation type
    if hi != "":
        res = hi
        key += "1"
    else:
        key += "0"

    if lo != "":
        res = lo
        key += "1"
    else:
        key += "0"

    if eq != "":
        res = eq
        key += "1"
    else:
        key += "0"

    # use key to get operation type
    if key == "001":
        op = "="
    if key == "010":
        op = "<"
    if key == "011":
        op = "<="
    if key == "100":
        op = ">"
    if key == "101":
        op = ">="
    if key == "110":
        op = "<>"

    return [res, op]

# /////////////////////////////////////////////////////////////////////////
def subDurTranslate(fact1, fact2, result):
    durationToFunc = {"*YEARS"   : "years"   , "*Y" : "years"   , 
                      "*MONTHS"  : "months"  , "*M" : "months"  , 
                      "*DAYS"    : "Days"    , "*D" : "Days"    , 
                      "*HOURS"   : "Hours"   , "*H" : "Hours"   , 
                      "*MINUTES" : "minutes" , "*MN": "minutes" , 
                      "*SECONDS" : "Seconds" , "*S" : "Seconds" , 
                      "*MSECONDS": "mseconds", "*MS": "mseconds" }

    # get the factor that has a [:] 
    if ":" in fact2:
        # on factor 2 operation returns a date
        arr = fact2.split(":")
        return "{0} -= %{1}({2});\n".format(result, arr[1], arr[0])
    else:
        #on result operation returns an integer
        arr = result.split(":")
        return "{0} = %diff({1}:{2}:{3});\n".format(arr[0], fact1, fact2, arr[1])

# /////////////////////////////////////////////////////////////////////////
def mathOperation(op, fact1, fact2, result, HI, LO, EQ):
    global gblMVRStr

    oper = {"DIV":"/", "MULT":"*", "ADD":"+", "SUB":"-",
            "DIV(H)":"/", "MULT(H)":"*", "ADD(H)":"+", "SUB(H)":"-"}
    ret = ""

    if fact1 != "":
        ret += "{0} = {1} {2} {3};\n".format(result, fact1, oper[op], fact2)
    else:
        ret += "{0} {1}= {2};\n".format(result, oper[op], fact2)

    if HI != "":
        ret += "*in{0} = ({1} > 0);\n".format(itmArr[4], itmArr[1])
    if LO != "":
        ret += "*in{0} = ({1} < 0);\n".format(itmArr[5], itmArr[1])
    if EQ != "":
        ret += "*in{0} =({1} = 0);\n".format(itmArr[6], itmArr[1])

    # assign MVR value
    if op == "DIV":
        if fact1 != "":
            gblMVRStr = "%rem({0}: {1});\n".format(fact1, fact2)
        else:
            gblMVRStr = "%rem({0}: {1});\n".format(result, fact2)

    # return new freeformat math operaton
    return ret

# /////////////////////////////////////////////////////////////////////////
def mvrToBIF(result):
    global gblMVRStr
    return  "{0} = {1}".format(result, gblMVRStr)

# /////////////////////////////////////////////////////////////////////////
def cLineBreaker(line):
    # RPG C line format
    # CL0N01Factor1+++++++Opcode&ExtFactor2+++++++Result++++++++Len++D+HiLoE
    # cann                 z-add     .050          rate              4 3
    global gblTmp
    global gblDataDivision
    global gblInLineDeclare
    setLineControl = ""
    controlNtoConst = ""
    lin = line.strip()
    ret = []

    # main instruction operations ( factors )
    Opcode = lin[20: 30].strip()
    result = lin[44:58].strip()
    fact1 = lin[6:20].strip()
    fact2 = lin[30:44].strip()

    # line control
    L0 = lin[1:3].strip().upper()
    N = lin[3:4].strip().upper()
    iO1 = lin[4:6].strip().upper()

    # dynamic result variable declaration
    Len = lin[58:63].strip()
    d = lin[63:65].strip()

    # result indicators
    hi = lin[65:67].strip()
    lo = lin[67:69].strip()
    eq = lin[69:71].strip()

    # normalize N position
    if N == "":
        controlNtoConst = "*On"
    else:
        controlNtoConst = "*Off"

    # handle do blocks
    if Opcode == "DO":
        if (N != "" or iO1 != "" or L0 != "") and (fact2 == "" and result == ""):
            if L0 == "":
                if N == "":
                    return ["IF", "*in{0} = *On".format(iO1)]
                else:
                    return ["IF", "*in{0} = *Off".format(iO1)]
            else:
                return ["IF", "*in{0} = *On".format(L0)]
        else:
            if fact2 != "" and result != "":
                return ["FOR", "{0} to {1}".format(result, fact2)]
            else:
                return ["FOR", "1 to {1}".format(result, fact2)]

    # handl lines that dont use factor 1 and 2
    if "EVAL" in Opcode or Opcode == "IF" or Opcode == "FOR" or Opcode == "DOW" or Opcode == "DOU" or Opcode == "WHEN":
        return [Opcode, lin[30:75].strip()]


    #-------------------------------------------------------------------------------------------------
    # remove subroutine (SR) symbol on LO
    # this is legacy code form RPG2
    if L0 == "SR":
        L0 = ""

    # set up if statment for control line
    if N != "" or iO1 != "":
        if L0 == "":
            setLineControl = "IF *in{0} = {1};".format(iO1, controlNtoConst)
        else:
            if L0 == "AN" or L0 == "OR":
                if L0 == "AN":
                    setLineControl = "And"
                else:
                    setLineControl = "Or"
            if N != "":
                setLineControl = "IF {1} *in{0} = {2}; // this needs to be combined".format(iO1, setLineControl,controlNtoConst)
            else:
                setLineControl = "IF {1} *in{0} = {2}; // this needs to be combined".format(iO1, setLineControl, controlNtoConst)

    # handle inline declaration
    if Len != "" or d != "":
        if (result in gblInLineDeclare) == False:
            # save varialbe name to prevent redeclaration
            gblInLineDeclare.append(result)

            # add varialbe declaration to data division
            if Len != "" and d != "":
                gblDataDivision += "Dcl-s {0} zoned({1}: {2});\n".format(result, Len, d)
            else:
                gblDataDivision += "Dcl-s {0} char({1});\n".format(result, Len)

    # prep the return array
    if setLineControl == "":
        if Opcode == "SETON" or Opcode == "SETOFF":
            ret = [Opcode, hi, lo, eq]
        else:
            ret = [Opcode, result, fact1, fact2, hi, lo, eq]
    else:
        ret = [setLineControl, Opcode, result, fact1, fact2, hi, lo, eq]

    return ret

# /////////////////////////////////////////////////////////////////////////
def dLineBreaker(line):
    #DName+++++++++++ETDsFrom+++To/L+++IDc.Keywords+++++++++++++++++++++++++ 
    global gblTmp
    setLineControl = ""
    controlNtoConst = ""
    lin = line.strip()
    decloration = ""
    ret = []

    lin = line.upper().strip()
    varName = lin[1: 16].strip()
    strucTy = lin[16: 17].strip()
    fildTyp = lin[18: 21].strip()
    numFrom = lin[21: 27].strip()
    varSize = lin[27: 34].strip()
    varType = lin[34: 35].strip()
    decSize = lin[35: 37].strip()
    keywords = lin[39: 72].strip()

    # set decloration keyword
    if fildTyp == "S":
        decloration = "Dcl-s"
    else:
        if fildTyp == "C":
            decloration = "Dcl-c"
        else:
            if fildTyp == "DS":
                decloration = "Dcl-Ds"

                if strucTy != "":
                    if strucTy == "U":
                        decloration += " DtaAra"
                    else:
                        if strucTy == "S":
                            decloration += " PSDS"
            else:
                decloration = ""

    if varType == "" or varType == "A":
        if decSize != "":
            varType = "ZONED"
        else:
            if "VARYING" in keywords:
                varType = "VARCHAR"
            else:
                varType = "CHAR"
    else:
        if varType == "T":
            varType = "TIME"
        else:
            if varType == "D":
                varType = "DATE"
            else:
                if varType == "N":
                    varType = "IND"
                else:
                    if varType == "P":
                        varType = "PACKED"
                    else:
                        if varType == "Z":
                            varType = "TIMESTAMP"
                        else:
                            if varType == "S":
                                varType = "ZONED"
                            else:
                                if varType == "I":
                                    varType = "INT"
                                else:
                                    if varType == "F":
                                        varType = "FLOAT"



    # setup returning array
    if decloration != "":
        ret = [decloration, varName, varType, varSize, decSize, keywords, ""]
    else:
        ret = [varName, numFrom, varType, varSize, decSize, keywords, "*"]

    return ret

# /////////////////////////////////////////////////////////////////////////
def fLineBreaker(line):
    line = line.upper()
    fileName = ""
    acc = ""
    access = ""
    keywords = ""
    divice = ""
    ret = []
    accLib = {"I":"usage(*input)", "O":"usage(*output)", "U":"usage(*update)", "C":"usage(*input: *update: *output)"}

    fileName = line[1: 11].strip()
    acc = line[11:12].strip()
    keywords = line[38: 74].strip()
    divice = line[30: 37].strip()

    # display file given do not apply access
    if "WORKSTN" in divice or "PRINTER" in divice:
        divice += (" " + keywords).strip()
        return [fileName, "", divice]
    else:
        #apply file acces 
        if acc in accLib :
            access = accLib[acc]
        else:
            access = ""

    ret = [fileName, access, keywords]
    return ret

# /////////////////////////////////////////////////////////////////////////
def cComposer(itmArr, originalLine):
    global gblProcedureDivision
    global gblIndent
    
    COMPARITOR = {"LE":"<=","GE":">=","LT":"<","GT":">","EQ":"=","NE":"<>"}
    OnConditinalLine = False
    doAddIndent = False
    doIgnoreIndent = False
    outputLine = ""

    # notihing to compose
    if itmArr is None:
        return
    if len(itmArr) == 0:
        return

    # arry contains a RPG line 
    if len(itmArr) == 1:
        outputLine += itmArr[0]

    if "IF " in itmArr[0]:
        outputLine += "{0}\n{1}    ".format(itmArr[0], gblIndent)
        OnConditinalLine = True
        itmArr = itmArr[1:]

    # add indent to the current line
    if itmArr[0] == "IF" or itmArr[0] == "FOR" or itmArr[0] == "DOW" or itmArr[0] == "DOU" or itmArr[0] == "SELECT":
        doAddIndent = True

    #print("------------------------------\n{0}\n-----------------------------".format(itmArr))

    # These op codes have already been processed in setup()
    if itmArr[0] == "KLIST" or itmArr[0] == "KFLD" or itmArr[0] == "PLIST" or itmArr[0] == "PARM":
        return

    #[Opcode, result, fact1, fact2, hi, lo, eq]
    # comment out compiller directive
    if "/SPACE" in originalLine:
        gblProcedureDivision += "// {0}\n".format(originalLine)
        return
    if itmArr[0] == "GOTO" or itmArr[0] == "TAG":
        gblProcedureDivision += "{0}\n".format(originalLine)
        return
    if itmArr[0] == "END":
        gblIndent = gblIndent[4:]
        gblProcedureDivision += "{0}\n".format(originalLine)
        return


    # on sql operation
    if originalLine[1] == '~':
        outputLine = gblSQLBlock[originalLine[1:].strip()] + "\n"
    if itmArr[0] == "MVR":
        outputLine += mvrToBIF(itmArr[1])
    if itmArr[0] == "LEAVESR":
        outputLine += "return;\n"
    if itmArr[0] == "LEAVE":
        outputLine += "leave;\n"
    if itmArr[0] == "CLEAR":
        outputLine += "clear {0};\n".format(itmArr[1])
    if itmArr[0] == "WHENEQ" or itmArr[0] == "WHENNE" or itmArr[0] == "WHENLE" or itmArr[0] == "WHEGE" or itmArr[0] == "WHENLT" or itmArr[0] == "WHENGT":
        outputLine += "when {0} {1} {2};\n".format(itmArr[2], getRPG3_ComparisonOp(itmArr[0]), itmArr[3])
    if itmArr[0] == "SCAN":
        if len(itmArr[1]) == 0:
            outputLine += "%Scan({0}: {1}));  // use %found() to check if string was found\n".format(itmArr[2], itmArr[3])
        else:
            outputLine += "{2} = %Scan({0}: {1});\n".format(itmArr[2], itmArr[3], itmArr[1])
    if itmArr[0] == "EXFMT":
        outputLine += "write {0}; // write to display\n".format(itmArr[3])
    if itmArr[0] == "BITOFF":
        outputLine += "{0} = %Bitand({0}: %Bitnot({1}));".format(itmArr[1], itmArr[3])
    if itmArr[0] == "BITON":
        outputLine += "{0} = %Bitor({0}: {1});".format(itmArr[1], itmArr[3])
    if itmArr[0] == "TESTB":
        if itmArr[4] != "":
            outputLine += "*in{2} = %Bitand({0}: {1}) = x'00';\n".format(itmArr[1], itmArr[3], itmArr[4])
        else:
            if itmArr[6] != "":
                outputLine += "*in{2} = %Bitand({0}: {1}) = {1};\n".format(itmArr[1], itmArr[3], itmArr[6])
            else:
                outputLine += "*in{2} = %Bitand({0}: {1}) <> x'00' and  %Bitand({0}: {1}) <> {1};\n".format(itmArr[1], itmArr[3], itmArr[5])
    if itmArr[0] == "ANDEQ" or itmArr[0] == "ANDNE" or itmArr[0] == "ANDLT" or itmArr[0] == "ANDLE" or itmArr[0] == "ANDGT" or itmArr[0] == "ANDGE":
        outputLine += "and {0} {2} {1} // this is apart of the if/loop block\n".format(itmArr[2], itmArr[3], getRPG3_ComparisonOp(itmArr[0]))
    if itmArr[0] == "OREQ" or itmArr[0] == "ORNE" or itmArr[0] == "ORLT" or itmArr[0] == "ORLE" or itmArr[0] == "ORGT" or itmArr[0] == "ORGE":
        outputLine += "or {0} {2} {1} // this is apart of the if/loop block\n".format(itmArr[2], itmArr[3], getRPG3_ComparisonOp(itmArr[0]))
    if itmArr[0] == "SUBDUR":
        outputLine += subDurTranslate(itmArr[2], itmArr[3], itmArr[1])
    if itmArr[0] == "ADDDUR":
        outputLine += subDurTranslate(itmArr[2], itmArr[3], itmArr[1])
    if itmArr[0] == "CAT":
        outputLine += "{0} = {1} + {2};\n".format(itmArr[1], itmArr[2], itmArr[3])
    if "OCCUR" in itmArr[0]:
        if itmArr[2] == "":
            outputLine += "{0} = %Occur({1});\n".format(itmArr[1], itmArr[3])
        else:
            outputLine += "%Occur({1}) = {0};\n".format(itmArr[2], itmArr[3])
        if  itmArr[6] != "":
            outputLine += "\n{1}*in{0} = %Equals();\n".format(itmArr[6], gblIndent)
    if "MOVEA" in itmArr[0]:
        outputLine += "{0} = {1};\n".format(itmArr[1], itmArr[3])
    if "COMP" in itmArr[0]:
        indResult = translateIndicators(itmArr[4],itmArr[5],itmArr[6])
        outputLine += "*in{0} = ({1} {3} {2});\n".format(indResult[0], itmArr[2], itmArr[3], indResult[1])
    if "Z-ADD" in itmArr[0] or itmArr[0] == "MOVE":
        outputLine += "{0} = {1};\n".format(itmArr[1], itmArr[3])
    if "Z-SUB" in itmArr[0]:
        outputLine += "{0} = (-1 * {1});\n".format(itmArr[1], itmArr[3])
    if itmArr[0] == "ADD" or itmArr[0] == "SUB" or itmArr[0] == "DIV" or itmArr[0] == "MULT" or itmArr[0] == "ADD(H)" or itmArr[0] == "SUB(H)" or itmArr[0] == "DIV(H)" or itmArr[0] == "MULT(H)":
        outputLine += mathOperation(itmArr[0], itmArr[2], itmArr[3], itmArr[1], itmArr[4], itmArr[5],itmArr[6])
    if itmArr[0] == "MOVEL":
        outputLine += "// MOVEL Operation: check type before adding spaces/zeros\n{0} {1} = {2}\n".format(itmArr[0], itmArr[1], itmArr[3])
    if itmArr[0] == "EXSR":
        outputLine += "{0}();\n".format(itmArr[3])
    if itmArr[0] == "SETON" or itmArr[0] == "SETOFF":
        for ind in itmArr[1:]:
            if ind != "":
                if "ON" in itmArr[0]:
                    outputLine += "*in{0} = *On;\n".format(ind)
                else:
                    outputLine += "*in{0} = *Off;\n".format(ind)
    if itmArr[0] == "EXCEPT":
        outputLine += "write {0}; // write to report format\n".format(itmArr[3])
    if itmArr[0] == "CLOSE" or itmArr[0] == "OPEN":
        outputLine += "{0} {1};\n".format(itmArr[0], itmArr[3])
    if itmArr[0] == "CALL"  or itmArr[0] == "CALLP":
        outputLine += "{0} // call to external procedure or program\n".format(getExternalProcCall(itmArr[3]))
    if itmArr[0] == "WRITE" or itmArr[0] == "UPDATE" or itmArr[0] == "DELETE":
        outputLine += "{0} {1};\n".format(itmArr[0], itmArr[3])
        if itmArr[4] != "":
            outputLine += "{1}*in{0} = %error();\n".format(itmArr[4], gblIndent)
        if itmArr[5] != "":
            outputLine += "{1}*in{0} = %eof();\n".format(itmArr[5], gblIndent)
    if "EVAL" in itmArr[0]:
        outputLine += "{0};\n".format(itmArr[1])
    if "READ" in itmArr[0] or itmArr[0] == "READE" or itmArr[0] == "READC" or itmArr[0] == "READPE":
        if itmArr[2] == "":
            outputLine += "{0} {1};\n".format(itmArr[0], itmArr[3])
        else:
            outputLine += "{0} {1} {2};\n".format(itmArr[0], getKeyString(itmArr[2]), itmArr[3])
        if itmArr[4] != "":
            outputLine += "{1}*in{0} = %error();\n".format(itmArr[4], gblIndent)
        if itmArr[6] != "":
            outputLine += "{1}*in{0} = %eof();\n".format(itmArr[6], gblIndent)
    if itmArr[0] == "ELSE":
        outputLine += "{0};\n".format(itmArr[0])
    if itmArr[0] == "IF" or itmArr[0] == "FOR" or itmArr[0] == "DOW" or itmArr[0] == "DOU" or itmArr[0] == "WHEN":
        outputLine += "{0} {1};\n".format(itmArr[0], itmArr[1])
    if itmArr[0] == "IFEQ" or itmArr[0] == "IFNE" or itmArr[0] == "IFGT" or itmArr[0] == "IFLT" or itmArr[0] == "IFGE" or itmArr[0] == "IFLE":
        doAddIndent = True
        outputLine += "IF {1} {3} {2};\n".format(itmArr[0], itmArr[2], itmArr[3], COMPARITOR[itmArr[0][2:]])
    if itmArr[0] == "DOWEQ" or itmArr[0] == "DOWNE" or itmArr[0] == "DOWGT" or itmArr[0] == "DOWLT" or itmArr[0] == "DOWGE" or itmArr[0] == "DOWLE":
        doAddIndent = True
        outputLine += "DOW {1} {3} {2};\n".format(itmArr[0], itmArr[2], itmArr[3], COMPARITOR[itmArr[0][3:]])
    if itmArr[0] == "DOUEQ" or itmArr[0] == "DOUNE" or itmArr[0] == "DOUGT" or itmArr[0] == "DOULT" or itmArr[0] == "DOUGE" or itmArr[0] == "DOULE":
        doAddIndent = True
        outputLine += "DOU {1} {3} {2};\n".format(itmArr[0], itmArr[2], itmArr[3], COMPARITOR[itmArr[0][3:]])
    if itmArr[0] == "RETURN" or itmArr[0] == "ENDIF" or itmArr[0] == "ENDDO" or itmArr[0] == "ENDFOR" or itmArr[0] == "ENDSL" or itmArr[0] == "SELECT" or itmArr[0] == "OTHER":
        outputLine += "{0};\n".format(itmArr[0])
    if itmArr[0] == "CHAIN" or itmArr[0] == "CHAIN(E)" or itmArr[0] == "CHAIN(N)":
        outputLine += "{0} {1} {2};\n".format(itmArr[0], getKeyString(itmArr[2]), itmArr[3])
        if itmArr[4] != "":
            outputLine += "{1}*in{0} = (%found() = *Off);\n".format(itmArr[4], gblIndent)
        if itmArr[5] != "":
            outputLine += "{1}*in{0} = %error();\n".format(itmArr[5], gblIndent)
    if itmArr[0] == "SETLL" or itmArr[0] == "SETLL(E)" or itmArr[0] == "SETGT" or itmArr[0] == "SETGT(E)":
        outputLine += "{0} {1} {2};\n".format(itmArr[0], getKeyString(itmArr[2]), itmArr[3])
        if itmArr[4] != "":
            outputLine += "{1}*in{0} = (%found() = *Off);\n".format(itmArr[4], gblIndent)
        if itmArr[5] != "":
            outputLine += "{1}*in{0} = %error();\n".format(itmArr[5], gblIndent)
    if itmArr[0] == "CABEQ" or itmArr[0] == "CABNE" or itmArr[0] == "CABGT" or itmArr[0] == "CABLT" or itmArr[0] == "CABGE" or itmArr[0] == "CABLE":
        outputLine += "IF {1} {3} {2};\n    {4};\nENDIF;\n".format(itmArr[0], itmArr[2], itmArr[3], COMPARITOR[itmArr[0][3:]], itmArr[1])
    if itmArr[0] == "XFOOT":
        outputLine += "{0} = %xfoot({1});\n".format(itmArr[1],itmArr[3])
    if itmArr[0] == "XLATE":
        outputLine += "{0} = %xlate({1}: {2});\n".format(itmArr[1], itmArr[2], itmArr[3])
    if itmArr[0] == "TIME" or itmArr[0] == "DATE":
        outputLine += "{1} = %{0}();\n".format(itmArr[0], itmArr[1])
    if itmArr[0] == "LOOKUP":
        if itmArr[1] == "":
            outputLine += "*in{1} = %{0}({2}: {3});\n".format(itmArr[0], itmArr[6], itmArr[2], itmArr[3])
        else:
            outputLine += "*in{1} = %{0}({2}: {3}: {4});\n".format(itmArr[0], itmArr[6], itmArr[2], itmArr[3], itmArr[4])
    if itmArr[0] == "BEGSR":
        doAddIndent = True
        outputLine += "// /////////////////////////////////////////////////////////////////////////\nDcl-Proc {0};\n".format(itmArr[2])
    if itmArr[0] == "ENDSR":
        outputLine += "End-Proc;\n"
    if itmArr[0] == "SORTA":
        outputLine += "SORTA {0};\n".format(itmArr[3])
    
    if OnConditinalLine == True:
        outputLine += "{0}ENDIF;\n".format(gblIndent)

    # remove indent
    if "END" in itmArr[0]:
        gblIndent = gblIndent[4:]

    # unable to compose line return original RPG line
    if outputLine.strip == "":
        # nothing to do just print the line
        outputLine = originalLine + "\n"
    else:
        # add Indent when needed
        if doIgnoreIndent == False:
            outputLine = gblIndent + outputLine

    #add line to output program
    gblProcedureDivision += outputLine
    print(outputLine.rstrip())

    # add indent
    if doAddIndent == True:
        gblIndent += "    "
            
# /////////////////////////////////////////////////////////////////////////
def fComposer(itmArr):
    global gblFileDivision
    outline = ""

    # [fileName, access, keywords]

    if itmArr[0] != "" and itmArr[1] != "" and itmArr[2] != "":
        outline += "Dcl-f {0} {1} {2};\n".format(itmArr[0], itmArr[1], itmArr[2])
    else:
        if itmArr[0] != "" and itmArr[1] != "" and itmArr[2] == "":
            outline += "Dcl-f {0} {1};\n".format(itmArr[0], itmArr[1])
        else:
            if itmArr[0] != "" and itmArr[1] == "" and itmArr[2] != "":
                outline += "Dcl-f {0} {1};\n".format(itmArr[0], itmArr[2])
            else:
                if itmArr[0] == "" and itmArr[1] == "" and itmArr[2] != "":
                    outline += "                {0};\n".format(itmArr[2])
    
    gblFileDivision += outline
    print(outline.rstrip())
            
# /////////////////////////////////////////////////////////////////////////
def dComposer(itmArr):
    global gblDataDivision
    global gblTmp
    from_ = 0
    vsize = 0
    outputLine = ""
    
    # convert From and Variable size to inategers
    # but only for datastructure variables
    if itmArr[0] in ["Dcl-s","Dcl-c","Dcl-Ds"] == False:
        if itmArr[1] != "":
            from_ = int(itmArr[1])
        else:
            from_ = 0
        if itmArr[3] != "":
            vsize = int(itmArr[3])
        else:
            vsize = 0

    # setup standard varialbes
    if itmArr[0] == "Dcl-s" or itmArr[0] == "Dcl-c":
        if gblTmp == "#":
            outputLine += "End-Ds;\n"
            gblTmp = ""

        # format standard variables
        if itmArr[2] == "ZONED" or itmArr[2] == "PACKED" or itmArr[2] == "INT":
            outputLine += "{0} {1} {2}({3}: {4});\n".format(itmArr[0],itmArr[1],itmArr[2],itmArr[3],itmArr[4])
        else:
            if itmArr[2] == "IND" or itmArr[2] == "DATE" or itmArr[2] == "TIME" or itmArr[2] == "TIMESTAMP":
                outputLine += "{0} {1} {2};\n".format(itmArr[0],itmArr[1],itmArr[2])
            else:
                outputLine += "{0} {1} {2}({3});\n".format(itmArr[0],itmArr[1],itmArr[2],itmArr[3])
    
    #setup data structures 
    if "Dcl-Ds" in itmArr[0]:
        #check to see if the datastructure is a program/dataArea/file status data structure
        if itmArr[0] != "Dcl-Ds":
            tarr = itmArr[0].split(" ")
            itmArr[0] = tarr[0]
            
        # at end of old data structure and start of new one
        # add a end-ds before adding a delaration
        if gblTmp == "#":
            outputLine += "End-Ds;\n"

        # set flag that indicates datastruct declaratrion
        gblTmp = "#"
        
        # set datastructure name
        if itmArr[1] == "":
            outputLine += "Dcl-ds *n;\n"
        else:
            outputLine += "Dcl-ds {0};\n".format(itmArr[1])

    # setup fields for data structure
    if itmArr[6] == "*":
        LENGTH = abs(from_ - vsize) + 1
        if itmArr[2] == "CHAR":
            outputLine += "    {0} {2}({3}) pos({1});\n".format(itmArr[0], itmArr[1], itmArr[2], LENGTH)
        if itmArr[2] == "ZONED":
            outputLine += "    {0} {2}({3}: {4}) pos({1});\n".format(itmArr[0], itmArr[1], itmArr[2], LENGTH, itmArr[4])
        if itmArr[2] == "":
            outputLine += "    {0} {2};\n".format(itmArr[0], itmArr[1])
    
    gblDataDivision += outputLine
    print(outputLine.rstrip())

# /////////////////////////////////////////////////////////////////////////
def rectifier(lines):
    global gblFileDivision
    global gblDataDivision
    global gblProcedureDivision
    global gblSQLBlock
    spec = ""
    Espec = ""
    Ospec = ""
    ret = ""
    arr = []

    for lin in lines:
        lin = lin.strip().upper()

        spec = lin[0: 1]

        # do nothing on these conditions
        if len(lin) < 2:
            continue
        if lin[1] == "*":
            continue

        # perform spec operations
        if spec == "C":
            arr = cLineBreaker(lin)
            #print(arr)
            cComposer(arr, lin)
        else:
            if spec == "D":
                arr = dLineBreaker(lin)
                #print(arr)
                dComposer(arr)
            else:
                if spec == "F":
                    arr = fLineBreaker(lin)
                    fComposer(arr)
                else:
                    if spec == "H":
                        gblFileDivision += "Ctl-Opt " + lin[1:].strip() + ";\n"
                    else:
                        gblProcedureDivision += lin + "\n"
                
    
    # combine RPG divisions into final program
    ret = ("**free\nCtl-Opt DFTACTGRP(*No);\n" + 
          gblFileDivision + 
          gblDataDivision + 
          gblProcedureDivision)

    # final cleanup section
    # replace any rpg style comments to C style comments
    if "\n*" in ret:
        ret = ret.replace("\n*","\n//")

    # fix any indicators that where commented by mistake
    if "\n//in" in ret:
        ret = ret.replace("\n//in","\n*in")

    return ret

# /////////////////////////////////////////////////////////////////////////
# go through sorce to get all Klists 
def setup(lines):
    global gblTmp
    global gblProcedureDivision
    global gblProgramName
    global gblSQLBlock
    setLineControl = ""
    controlNtoConst = ""
    entryParamiters = ""
    ret = []
    lineCnt = 0
    sqlKey = ""

    for line in lines:
        lin = line.strip().upper()

        # do nothon on these conditions
        if len(lin) < 2:
            lineCnt += 1
            continue
        if lin[1] == "*":
            lineCnt += 1
            continue

        # main instruction operations ( factors )
        Opcode = lin[20: 30].strip()
        result = lin[44:58].strip()
        fact1 = lin[6:20].strip()
        fact2 = lin[30:44].strip()

        # dynamic result variable declaration
        Len = (lin[58:63]).strip()
        d = (lin[63:65]).strip()

        # setup program paramiters
        if Opcode == "PLIST" and fact1 == "*ENTRY":
            gblTmp = "MAIN"
        if gblTmp == "MAIN" and Opcode == "PARM":
            if d == "":
                entryParamiters += "    {0} char({1});\n".format(result, Len)
            else:
                entryParamiters += "    {0} zoned({1}: {2});\n".format(result, Len, d)

        # on klist and kfld return nothing (ret remains blank)
        if Opcode == "KLIST" or Opcode == "KFLD":
            if Opcode == "KLIST":
                gblTmp = fact1
                addkeyList(fact1, "")
            else:
                addkeyList(gblTmp, result)
        
        if (Opcode == "CALL" or Opcode == "CALLP" or Opcode == "PARM") and Opcode != "PLIST":
            if gblTmp == "CALL" or gblTmp == "CALLP":
                gblTmp = fact1
                addkeyList(fact1, "")
            else:
                addCallParamList(gblTmp, result)

        if lin[:10] == "C/EXEC SQL" or lin[:10] == "C/END-EXEC" or lin[:2] == "C+":
            if lin[:10] == "C/EXEC SQL":
                sqlKey = "~{0}".format(lineCnt)
                addSQLBlock(sqlKey, lin[2:])
                lines[lineCnt] = "C" + sqlKey
            else:
                if lin[:10] == "C/END-EXEC":
                    addSQLBlock(sqlKey, ";")
                else:
                    addSQLBlock(sqlKey, lin[2:])

                lines[lineCnt] = "C"

        lineCnt += 1


    if entryParamiters != "":
        gblProcedureDivision += "Dcl-Pr Main extpgm('{1}');\n{0}End-Pr;\n\nDcl-Pi Main;\n{0}End-Pi;\n".format(entryParamiters, gblProgramName)

# /////////////////////////////////////////////////////////////////////////
def Main():
    global gblProgramName
    fName =""

    arg = sys.argv
    
    if len(arg) == 2:
        tarr = arg[1].split("\\")

        # generate new file name
        fname = tarr[len(tarr)-1:][0]
        fname = (fname.split("."))[0]
        gblProgramName = fname
        fname = "{0}_free.rpg".format(fname)

        # clear the output file
        clearFile(fname)

        lines = read(arg[1])

        # process the RPG file
        setup(lines)
        out = rectifier(lines)
        
        # save result
        write(fname, out)

# /////////////////////////////////////////////////////////////////////////
if __name__ == "__main__":
    Main()
