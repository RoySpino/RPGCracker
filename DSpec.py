import re

class D_Composer:
    gblTmp = ""
    gblIndent = ""
    gblProgramName = ""
    gblSQLBlock = {"": ""}
    gblMVRStr = ""
    gblGOTOLst = []
    gblEndBlockLst = []
    inDataStruct:bool = False
    onStandAlone:bool = False

    # /////////////////////////////////////////////////////////////////////////
    def dComposer(self, line:str) -> str:
        self.gblTmp
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
        if (["Dcl-s","Dcl-c","Dcl-Ds"]).count(itmArr[0]) == 0:
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
            #setup data structures 
            self.onStandAlone = False
            self.inDataStruct = True
            if "Dcl-Ds" in itmArr[0]:
                #check to see if the datastructure is a program/dataArea/file status data structure
                if itmArr[0] != "Dcl-Ds":
                    tarr = itmArr[0].split(" ")
                    itmArr[0] = tarr[0]
                    
                # at end of old data structure and start of new one
                # add a end-ds before adding a delaration
                if self.gblTmp == "#":
                    outputLine += "End-Ds;\n"

                # set flag that indicates datastruct declaratrion
                self.gblTmp = "#"
                
                # set datastructure name
                if itmArr[1] == "":
                    outputLine += "Dcl-ds *n{0};\n".format(itmArr[5])
                else:
                    outputLine += "Dcl-ds {0}{1};\n".format(itmArr[1], itmArr[5])

            # setup fields for data structure
            if itmArr[6] == "*":
                LENGTH = abs(vsize - from_) + 1

                if "pos" in itmArr[5]:
                    if itmArr[2] == "CHAR":
                        outputLine += "    {0} Char({1}) {2};\n".format(itmArr[0], LENGTH, itmArr[5])
                    if itmArr[2] == "ZONED":
                        outputLine += "    {0} Zoned({1}: {2}) {3};\n".format(itmArr[0], LENGTH, itmArr[4], itmArr[5])
                    if itmArr[2] == "":
                        outputLine += "    {0} {2} {3};\n".format(itmArr[0], itmArr[1], itmArr[5])
                else:
                    if itmArr[2] == "CHAR":
                        outputLine += "    {0} Char({2}) pos({1}){3};\n".format(itmArr[0], itmArr[1], LENGTH, itmArr[5])
                    if itmArr[2] == "ZONED":
                        outputLine += "    {0} Zoned({2}: {3}) pos({1}){4};\n".format(itmArr[0], itmArr[1], LENGTH, itmArr[4], itmArr[5])
                    if itmArr[2] == "":
                        outputLine += "    {0} {1}{2};\n".format(itmArr[0], itmArr[1], itmArr[5])
            
        # write to data/ procedure division
        #print(outputLine.rstrip())
        return outputLine

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
    def checkForUnclosedDataStruct(self):
        return self.inDataStruct == True and self.onStandAlone == False

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

