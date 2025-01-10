import linecache
import sys
import platform
import re as reg
from CSpec import C_Composer
from DSpec import D_Composer
from FSpec import F_Composer
from PSpec import P_Composer

gblFileDivision = ""
gblDataDivision = ""
gblProcedureDivision = ""
gblParams = {"": []}
gblKeys = {"":[]}
gblInLineDeclare = []
gblProgramName = ""
gblSQLBlock = {"": ""}
gblMVRStr = ""
gblGOTOLst = []
gblEndBlockLst = []

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
    f = open(path, "r", encoding='UTF8')

    # use readlines to read all lines in the file
    # The variable "lines" is a list containing all lines in the file
    lines = f.readlines()

    # close the file after reading the lines.
    f.close()

    return lines

# /////////////////////////////////////////////////////////////////////////
def addGOTOList(TagName):
    global gblGOTOLst

    if (TagName in gblGOTOLst) == False:
        gblGOTOLst.append(TagName)

# /////////////////////////////////////////////////////////////////////////
def rectifier(lines):
    global gblFileDivision
    global gblDataDivision
    global gblProcedureDivision
    global gblSQLBlock
    spec:str = ""
    ret:str = ""
    val:str = ""
    oLine:str = ""
    onProc:bool = False
    onArrayInit:bool = False
    lineCnt:int = 0

    SpecC = C_Composer(gblKeys, gblSQLBlock, gblGOTOLst, gblParams)
    SpecD = D_Composer()
    SpecF = F_Composer()
    SpecP = P_Composer(SpecC, SpecD)

    for lin in lines:
        oLine = lin.rstrip()
        lin = lin.strip().upper()
        lineCnt += 1

        spec = lin[0: 1]

        # check if the line is a array init line
        if lineCnt > 1 and onArrayInit == False:
            if oLine[:2] == "**":
                onArrayInit = checkOnArrayLine(oLine)
            else:
                onArrayInit = False

        # on an array init line 
        if onArrayInit == True:
            gblProcedureDivision += "///   {0}\n".format(lin)
            continue



        # return a comment line
        if len(lin) > 1:
            if lin[0] == "*":
                lin = "{1}// {0}\n".format(lin[2:], SpecC.getIndent())
                gblProcedureDivision += lin
                continue
            
        # handle SPACE
        if "/SPACE" in lin.upper():
            gblProcedureDivision += "\n"
            continue

        # On P spec
        if onProc == True:
            SpecP.pComposer(lin)

            if SpecP.isEndOfProc() == True:
                gblProcedureDivision += SpecP.getProcedure()
                onProc = False
        else:
            # STANDARD processing without Procedures
            # do nothing on these conditions
            if len(lin) < 2:
                continue
            if lin[1] == "*":
                continue

            # perform spec operations
            if spec == "C":
                gblProcedureDivision += SpecC.cComposer(lin)
            else:
                if spec == "D":
                    val = SpecD.dComposer(lin)
                    gblDataDivision += val
                else:
                    if spec == "F":
                        gblFileDivision += SpecF.fComposer(lin)
                    else:
                        if spec == "H":
                            gblFileDivision += "Ctl-Opt " + lin[1:].strip() + ";\n"
                        else:
                            if spec == "P":
                                # Perform first and only p spec here
                                # P spec processing is handled in object
                                onProc = True
                                SpecP.pComposer(lin)
                            else:
                                gblProcedureDivision += (lin + "\n")

    # check for unclosed data structures
    if SpecD.checkForUnclosedDataStruct() == True:
        gblDataDivision = gblDataDivision + "End-Ds;\n"
    
    # save the inline variable declarations to data division
    gblDataDivision += SpecC.getDataDivision()

    
    # combine RPG divisions into final program
    ret = ("**free\nCtl-Opt DFTACTGRP(*No);\n" + 
          gblFileDivision + 
          gblDataDivision + 
          gblProcedureDivision)

    # collaps or*/and* opcodes
    ret = reg.sub(r"(;\r\n|;\r|;\n|\r\n|\r|\n)\s*(or|Or)", " Or", ret)
    ret = reg.sub(r"(;\r\n|;\r|;\n|\r\n|\r|\n)\s*(and|And)", " And", ret)

    # final cleanup section
    # replace any rpg style comments to C style comments
    #if "\n*" in ret:
    #    ret = ret.replace("\n*","\n//")

    #    # fix any indicators that where commented by mistake
    #    ret = ret.replace("\n//IN","\n*in")

    return ret

# /////////////////////////////////////////////////////////////////////////
# go through sorce to get all Klists 
def setup(lines):
    global gblProcedureDivision
    global gblProgramName
    global gblSQLBlock
    global gblSubroutine
    gblTmp:str = ""
    setLineControl:str = ""
    controlNtoConst:str = ""
    entryParamiters:str = ""
    first10:str = ""
    first3:str = ""
    oLine:str = ""
    lineCnt:int = 0
    sqlLinCnt:int = 0
    sqlKey:str = ""

    for line in lines:
        lin = line.strip().upper()
        lineCnt += 1

        # do nothing on these conditions
        if len(lin) < 2:
            continue
        if lin[0] == "*":
            continue

        # main instruction operations ( factors )
        Opcode = lin[20: 30].strip()
        result = lin[44:58].strip()
        fact1 = lin[6:20].strip()
        fact2 = lin[30:44].strip()
        first10 = lin[:10]
        first3 = lin[:3]

        # dynamic result variable declaration
        Len = (lin[58:63]).strip()
        d = (lin[63:65]).strip()


        # get sql comands
        if "/EXEC SQL" in first10 or "/END-EXEC" in first10 or "C+" in first3:
            if "/EXEC SQL" in first10:
                sqlKey = "~{0}".format(sqlLinCnt)
                addSQLBlock(sqlKey, lin[2:])
                lines[lineCnt-1] = "C" + sqlKey
            else:
                if "/END-EXEC" in first10:
                    addSQLBlock(sqlKey, ";")
                    sqlLinCnt += 1
                else:
                    addSQLBlock(sqlKey, lin[2:])

                lines[lineCnt-1] = "C"
            continue

        # get list of tags for goto's
        if Opcode == "GOTO" or Opcode == "TAG":
            if Opcode == "GOTO":
                addGOTOList(fact2)
            else:
                addGOTOList(fact1)
            continue

        # setup program paramiters
        if Opcode == "PLIST" and fact1 == "*ENTRY":
            gblTmp = "MAIN"
        if gblTmp == "MAIN" and Opcode == "PARM":
            if d == "":
                entryParamiters += "    {0} char({1});\n".format(result, Len)
            else:
                entryParamiters += "    {0} zoned({1}: {2});\n".format(result, Len, d)
            continue

        # on klist and kfld return nothing (ret remains blank)
        if Opcode == "KLIST" or Opcode == "KFLD":
            if Opcode == "KLIST":
                gblTmp = fact1
                addkeyList(fact1, "")
            else:
                addkeyList(gblTmp, result)
            continue
        
        if Opcode == "CALL" or Opcode == "CALLP" or Opcode == "PARM":
            if Opcode == "CALL" or Opcode == "CALLP":
                gblTmp = fact2
                addCallParamList(fact2, "", Opcode)
            else:
                addCallParamList(gblTmp, result, "")
            continue


    if entryParamiters != "":
        gblProcedureDivision += "Dcl-Pr Main extpgm('{1}');\n{0}End-Pr;\n\nDcl-Pi Main;\n{0}End-Pi;\n".format(entryParamiters, gblProgramName)

    return lines

# /////////////////////////////////////////////////////////////////////////
def checkOnArrayLine(line:str) -> bool:
    tline:str
    tline = line[:5]

    for itm in tline:
        if itm != "*":
            return True

    return False

# /////////////////////////////////////////////////////////////////////////
def addkeyList(keyName, value):
    global gblKeys

    if keyName in gblKeys:
        gblKeys[keyName].append(value)
    else:
        gblKeys[keyName] = [value]
        
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
def addCallParamList(keyName, value, opcode):
    global gblParams

    kname = ""

    # clean up call command by removing ['] 
    if "CALL" in opcode:
        kname = keyName.replace("'","")

    if kname in gblParams:
        gblParams[kname].append(value)
    else:
        gblParams[kname] = [value]

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
        fname = "{0}_free.rpgle".format(fname)

        # clear the output file
        clearFile(fname)

        lines = read(arg[1])

        # process the RPG file
        lines = setup(lines)
        out = rectifier(lines)
        
        # save result
        write(fname, out)

# /////////////////////////////////////////////////////////////////////////
if __name__ == "__main__":
    Main()
