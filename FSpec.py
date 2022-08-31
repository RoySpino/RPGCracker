class F_Composer:
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
    gblGOTOLst = []
    gblEndBlockLst = []

    def fComposer(self, line:str) -> str:
        outline = ""

        itmArr = self.fLineBreaker(line)

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
        
        print(outline.rstrip())
        return outline

    # /////////////////////////////////////////////////////////////////////////
    def fLineBreaker(self, line):
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
            divice += " " + (keywords).strip()
            return [fileName, "", divice]
        else:
            #apply file acces 
            if acc in accLib :
                access = accLib[acc]
            else:
                access = ""

        ret = [fileName, access, keywords]
        return ret