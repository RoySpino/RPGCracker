import re 

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
    gblKeywordList = []

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
    def keywordGenerator(self):
        return " ".join(self.gblKeywordList)
    
    # /////////////////////////////////////////////////////////////////////////
    def setKeywords(self, words):
        wds = words.strip()

        if len(wds) == 0:
            self.gblKeywordList = []
        else:
            wds = re.sub(r"\s+", " ", wds)
            self.gblKeywordList = wds.split(" ")

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
        fdesg = line[12:13].strip()
        fadd = line[14:15].strip()
        keyed = line[28:29].strip()
        keywords = line[38: 74].strip()
        divice = line[30: 37].strip()

        # setup keyword array
        self.setKeywords(keywords)

        # display file given do not apply access
        if "WORKSTN" in divice or "PRINTER" in divice:
            divice += " " + self.keywordGenerator()
            return [fileName, "", divice]
        else:
            #apply file acces 
            if fadd != "":
                if acc == "U":
                    access = "usage(*input: *update: *output)"
                else:
                    access = "usage(*input: *output)"
            else:
                if acc in accLib :
                    access = accLib[acc]
                else:
                    access = ""

        # apply [keyed] to file access
        if keyed != "":
            self.gblKeywordList  = ["Keyed"] + self.gblKeywordList
            keywords = self.keywordGenerator()

        # create string and return
        ret = [fileName, access, keywords]
        return ret
