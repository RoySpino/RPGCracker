from asyncio.windows_events import NULL
from doctest import OutputChecker
from CSpec import C_Composer
from DSpec import D_Composer

class P_Composer:
    hasEnded = True
    SpecC = NULL
    SpecD = NULL
    localDataDivision:str = ""
    localProcedureDivision:str = ""
    procName:str = ""
    
    def __init__(self, CSpecOBJ, DSpecOBJ):
        self.SpecC = CSpecOBJ
        self.SpecD = D_Composer(DSpecOBJ)

    # /////////////////////////////////////////////////////////////////////////
    def pComposer(self, line:str):
        linetype = line[0].upper()

        if linetype == "P":
            self.pLineBreaker(line)
        else:
            self.rectifyLine(line)

    # /////////////////////////////////////////////////////////////////////////
    def pLineBreaker(self, line) -> str:
        line = (line.upper()).ljust(20)
        proName = ""
        startEnd = ""

        proName = line[1: 16].strip()
        startEnd = line[18: 21].strip()

        if startEnd == "B" or startEnd == "E":
            if startEnd == "B":
                startEnd = f"\n// {('/'*55)}\nDcl-Proc {proName};"
                self.procName = startEnd
                self.hasEnded = False
        
                self.SpecD.resetGlobals()
                self.SpecD.addIndent()
            else:
                self.hasEnded = True

        return startEnd
        
    # /////////////////////////////////////////////////////////////////////////
    def rectifyLine(self, lin:str):
        spec:str = ""

        lin = lin.strip().upper()

        spec = lin[0: 1]

        # do nothing on these conditions
        if len(lin) < 2:
            return ""
        if lin[1] == "*":
            return ""

        # perform spec operations
        if spec == "C":
            self.localProcedureDivision += "    " + self.SpecC.cComposer(lin)
        else:
            if spec == "D":
                val = self.SpecD.dComposer(lin)
                self.localDataDivision += val
            else:
                # return a comment line
                if lin[0] == "*":
                    lin = "{1}// {0}\n".format(lin, self.SpecC.getIndent())
                    self.localProcedureDivision += lin
                else:
                    self.localProcedureDivision += lin

    # /////////////////////////////////////////////////////////////////////////
    def getProcedure(self) -> str:
        ret:str = ""

        # print(f"<{self.procName}>")
        # print(f"[{self.localDataDivision}]")
        # print(f">{self.localProcedureDivision}<")

        # check for unclosed data structures
        if self.SpecD.checkForUnclosedDataStruct() == True:
            self.localDataDivision = self.localDataDivision + self.SpecD.getClosingDclBlock()

        ret = "{0}\n{1}\n{2}End-Proc;".format(self.procName, 
                                                self.localDataDivision, 
                                                self.localProcedureDivision)
        return ret

    # /////////////////////////////////////////////////////////////////////////
    def isEndOfProc(self) -> bool:
        return self.hasEnded
