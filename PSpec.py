from asyncio.windows_events import NULL
from doctest import OutputChecker
from CSpec import C_Composer
from DSpec import D_Composer

class P_Composer:
    hasEnded = False
    SpecC = NULL
    SpecD = NULL
    loclProcedureDivision:str = ""
    localProcedureDivision:str = ""
    output:str = ""
    
    def __init__(self, CSpecOBJ, DSpecOBJ):
        self.SpecC = CSpecOBJ
        self.SpecD = DSpecOBJ

    # /////////////////////////////////////////////////////////////////////////
    def pComposer(self, line:str) -> str:
        itmArr = self.pLineBreaker(line)

        return "{0} {1};\n".format(itmArr[0], itmArr[1])

    # /////////////////////////////////////////////////////////////////////////
    def pLineBreaker(self, line):
        line = line.upper()
        proName = ""
        startEnd = ""

        proName = line[1: 16].strip()
        startEnd = line[18: 21].strip()

        if startEnd == "B":
            self.hasEnded = False
            startEnd = "\n// /////////////////////////////////////////////////////////////////////////\nDcl-Proc "
            self.output += startEnd + proName
        else:
            startEnd = "End-Proc"
            self.hasEnded = True

        return
        
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
            self.localProcedureDivision += self.SpecC.cComposer(lin)
        else:
            if spec == "D":
                val = self.SpecD.dComposer(lin)
                self.loclProcedureDivision += val
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

        ret = "{0}\n{1}\n{2}\nEnd-Proc;".format(self.output, 
                                                self.loclProcedureDivision, 
                                                self.localProcedureDivision)
        return ret

    # /////////////////////////////////////////////////////////////////////////
    def isEndOfProc(self) -> bool:
        return self.hasEnded