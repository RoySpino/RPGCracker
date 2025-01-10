import re

class D_Composer:
    gblTmp = ""
    gblIndent = ""
    gblProgramName = ""
    gblSQLBlock = {"": ""}
    gblMVRStr = ""
    gblDeclareBlock = ""
    gblGOTOLst = []
    gblEndBlockLst = []
    inDataStruct:bool = False
    onStandAlone:bool = False
    gblDSConst = {
        "FILE"   : "*FILE",
        "STATUS" : "*STATUS",
        "OPCODE" : "*OPCODE",
        "ROUTIN" : "*ROUTIN",
        "RECORD" : "*RECORD",
        "SIZE"   : "*SIZE",
        "PROC"   : "*PROC",
        "STATUS" : "*STATUS"}
    gblRetType = {
        "Time"   : "Time",
        "Date" : "Date",
        "Ind" : "Ind",
        "Packed" : "Packed({0}: {1})",
        "TimeStamp" : "TimeStamp",
        "Zoned"   : "Zoned({0}: {1})",
        "Int"   : "Int({0})",
        "Float" : "Float({0})",
        "Uns" : "Uns({0})"}

    def __init__(self, lDspec = None):
        if (lDspec is None) == False:
            self.gblIndent       = lDspec.gblIndent
            self.gblProgramName  = lDspec.gblProgramName
            self.gblSQLBlock     = lDspec.gblSQLBlock
            self.gblMVRStr       = lDspec.gblMVRStr
            self.gblDeclareBlock = lDspec.gblDeclareBlock
            self.gblEndBlockLst  = lDspec.gblEndBlockLst
            self.inDataStruct    = lDspec.inDataStruct
            self.onStandAlone    = lDspec.onStandAlone


    # /////////////////////////////////////////////////////////////////////////
    def dComposer(self, line:str) -> str:
        from_ = 0
        vsize = 0
        outputLine = ""
        keywrd = ""
        
        itmArr = self.dLineBreaker(line)
        itmArr[5] = " " + itmArr[5]
        # [varName, numFrom, varType, varSize, decSize, keywords, "*"]

        if "OVERLAY" in itmArr[5]:
            itmArr[5] = self.normalizeOverlay(itmArr[5])

        # convert [From] and [Variable size] to inategers
        # but only for datastructure variables
        if (["Dcl-s","Dcl-c","Dcl-Ds","Dcl-Pi","Dcl-Pr"]).count(itmArr[0]) == 0:
            if itmArr[1].isnumeric() == True:
                from_ = int(itmArr[1])
            else:
                from_ = 0
            if itmArr[3].isnumeric() == True:
                vsize = int(itmArr[3])
            else:
                vsize = 0

        # setup standard varialbes
        if itmArr[0] == "Dcl-s" or itmArr[0] == "Dcl-c":
            self.onStandAlone = True
            self.inDataStruct = False

            if self.gblTmp == "#":
                outputLine += "End-Ds;\n"
                self.gblTmp = ""

            # apply keywords
            if itmArr[5] != "":
                keywrd = (" " + itmArr[5]).rstrip()

            # format standard variables
            if itmArr[2] == "ZONED" or itmArr[2] == "PACKED" or itmArr[2] == "INT":
                outputLine += "{0} {1} {2}({3}: {4}){5};\n".format(itmArr[0],itmArr[1],itmArr[2],itmArr[3],itmArr[4], keywrd)
            else:
                if itmArr[2] == "IND" or itmArr[2] == "DATE" or itmArr[2] == "TIME" or itmArr[2] == "TIMESTAMP":
                    outputLine += "{0} {1} {2}{3};\n".format(itmArr[0],itmArr[1],itmArr[2], keywrd)
                else:
                    outputLine += "{0} {1} {2}({3}){4};\n".format(itmArr[0],itmArr[1],itmArr[2],itmArr[3], keywrd)
        else:
            #setup data structures / declareative blocks
            self.onStandAlone = False
            self.inDataStruct = True
            if "Dcl-Ds" in itmArr[0]:
                outputLine += self.setDatarationBlocks("Ds", itmArr)
                ##check to see if the datastructure is a program/dataArea/file status data structure
                #if itmArr[0] != "Dcl-Ds":
                #    tarr = itmArr[0].split(" ")
                #    itmArr[0] = tarr[0]
                #    
                ## at end of old data structure and start of new one
                ## add a end-ds before adding a delaration
                #if self.gblTmp == "#":
                #    outputLine += "End-Ds;\n"

                ## set flag that indicates datastruct declaratrion
                #self.gblTmp = "#"
                #
                ## set datastructure name
                #if itmArr[1] == "":
                #    outputLine += (f"Dcl-ds *n {itmArr[5]}").strip() +";\n"
                #else:
                #    outputLine += ("Dcl-ds {itmArr[1]} {itmArr[5]}").strip() +";\n"
            else:
                if "Dcl-Pr" in itmArr[0]:
                    outputLine += self.setDatarationBlocks("Pr", itmArr)
                else:
                    if "Dcl-Pi" in itmArr[0]:
                        outputLine += self.setDatarationBlocks("Pi", itmArr)

            

        # setup fields for data structure
        if itmArr[6] == "*" and self.onStandAlone == False:
            LENGTH = abs(vsize - from_) + 1

            # check if the item is a known datastructure position
            # this value does not need a POS key word
            if itmArr[1] in self.gblDSConst.keys():
                outputLine += "    {0} {1};\n".format(itmArr[0], self.gblDSConst[itmArr[1]])
            else:
                itmArr[2] = itmArr[2].upper()
                
                # setup PR/ PI blocks
                if itmArr[1] == "":
                    if itmArr[2] == "CHAR":
                        outputLine += f"    {itmArr[0]} Char({LENGTH}) {itmArr[5]}"
                    if itmArr[2] == "ZONED":
                        outputLine += f"    {itmArr[0]} Zoned({LENGTH}: {itmArr[4]}) {itmArr[5]}"
                    if itmArr[2] == "":
                        outputLine += f"    {itmArr[0]} {itmArr[1]} {itmArr[5]}"
                else:
                    # setup Data structurs
                    if itmArr[2] == "CHAR":
                        outputLine += f"    {itmArr[0]} Char({LENGTH}) pos({itmArr[1]}) {itmArr[5]}"
                    if itmArr[2] == "ZONED":
                        outputLine += f"    {itmArr[0]} Zoned({LENGTH}: {itmArr[4]}) pos({itmArr[1]}) {itmArr[5]}"
                    if itmArr[2] == "":
                        outputLine += f"    {itmArr[0]} {itmArr[1]} {itmArr[5]}"
                outputLine = f"    {outputLine.strip()};\n"
                
        # write to data/ procedure division
        # print(outputLine.rstrip())
        #print(line.rstrip())
        return (self.gblIndent + outputLine)

    # /////////////////////////////////////////////////////////////////////////
    def setDatarationBlocks(self, btype, itmArr) -> str:
        ret = ""
        returnType = ""

        #check to see if the datastructure is a program/dataArea/file status data structure
        if itmArr[0] != f"Dcl-{btype}":
            tarr = itmArr[0].split(" ")
            itmArr[0] = tarr[0]
            
        # at end of old data structure and start of new one
        # add a end before adding a delaration 
        # remove end statement from the list
        if self.gblTmp == "#":
            self.gblEndBlockLst.pop()
            ret += f"End-{btype};\n"

        # set flag that indicates datastruct declaratrion
        self.gblTmp = "#"
        
        # set return type
        if btype != "Ds":
            returnType = self.gblRetType[itmArr[2]]
            returnType = returnType.format(itmArr[3], itmArr[4])

        # set datastructure name
        if itmArr[1] == "":
            ret += (f"Dcl-{btype} *n {returnType}").strip() +";\n"
        else:
            ret += ("Dcl-{btype} {itmArr[1]} {itmArr[5]}").strip() +";\n"

        self.gblEndBlockLst.append(f"End-{btype}")
        self.gblDeclareBlock = btype
        return ret

    # /////////////////////////////////////////////////////////////////////////
    def dLineBreaker(self, line:str):
        #DName+++++++++++ETDsFrom+++To/L+++IDc.Keywords+++++++++++++++++++++++++ 
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
        keywords = lin[38: 74].strip()

        # set decloration keyword
        if fildTyp == "S":
            decloration = "Dcl-s"
        else:
            if fildTyp == "C":
                decloration = "Dcl-c"
            else:
                if fildTyp == "PR":
                    decloration = "Dcl-Pr"
                else:
                    if fildTyp == "PI":
                        decloration = "Dcl-Pi"
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
                                        decloration += ""


        # set data type
        if varType == "" or varType == "A":
            if decSize != "":
                varType = "Zoned"
            else:
                if "VARYING" in keywords:
                    varType = "Varchar"
                else:
                    varType = "Char"
        else:
            if varType == "T":
                varType = "Time"
            else:
                if varType == "D":
                    varType = "Date"
                else:
                    if varType == "N":
                        varType = "Ind"
                    else:
                        if varType == "P":
                            varType = "Packed"
                        else:
                            if varType == "Z":
                                varType = "TimeStamp"
                            else:
                                if varType == "S":
                                    varType = "Zoned"
                                else:
                                    if varType == "I":
                                        varType = "Int"
                                    else:
                                        if varType == "F":
                                            varType = "Float"
                                        else:
                                            if varType == "U":
                                                varType = "Uns"

                                            
        # setup returning array
        # return standard variable eclaration
        if decloration != "":
            ret = [decloration, varName, varType, varSize, decSize, keywords, ""]
        else:
            # return datastruct, prototype, procedure interface bodies
            ret = [varName, numFrom, varType, varSize, decSize, keywords, "*"]

        return ret

    # /////////////////////////////////////////////////////////////////////////
    def checkForUnclosedDataStruct(self):
        return self.inDataStruct == True and self.onStandAlone == False

    # /////////////////////////////////////////////////////////////////////////
    def addIndent(self):
        self.gblIndent += (" " * 4)

    # /////////////////////////////////////////////////////////////////////////
    def getClosingDclBlock(self):
        if len(self.gblEndBlockLst) > 0:
            # get and remove the end block statment form the list
            el = self.gblEndBlockLst.pop()

            return f"{self.gblIndent}{el};\n"
            
        return ""

    # /////////////////////////////////////////////////////////////////////////
    def normalizeOverlay(self, kewrds):
        ret:str = ""
        tmp:str = ""
        pos:str = ""
        getCmd:bool = False

        # use regex to remove consecutive white spaces
        # and replace them with a singe space
        tmp = kewrds.strip()
        tmp = re.sub("\s{1,}", " ", tmp)

        # remove overlay from keywords and rewrite
        # keyword string to have pos insted of overlay
        getCmd = (re.findall("(?i)overlay[(][^)]{1,}[)]", tmp))[0]
        ret = re.sub("(?i)overlay[(][^)]{1,}[)]", "", tmp)
        pos = (re.findall("\d{1,}",getCmd))[0]

        # setup new keyword string with pos insted of overlay
        # and cleanup string
        ret = "pos({0}) {1}".format(pos, ret)
        ret = (re.sub("\s{1,}", " ", ret)).strip()
        
        return ret
    
    # /////////////////////////////////////////////////////////////////////////
    def dataStructConst(self, keyword:str):
        return False

    # /////////////////////////////////////////////////////////////////////////
    def resetGlobals(self):
        self.gblTmp = ""
        self.gblIndent = ""
        self.gblProgramName = ""
        self.gblSQLBlock = {"": ""}
        self.gblMVRStr = ""
        self.gblGOTOLst = []
        self.gblEndBlockLst = []
        self.inDataStruct:bool = False
        self.onStandAlone:bool = False
