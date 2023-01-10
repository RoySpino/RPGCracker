from ast import Return
from ctypes.wintypes import BOOL
from pickle import TRUE


class C_Composer:
    gblProcedureDivision = ""
    gblDataDivision = ""
    gblKeys = {"":[]}
    gblSQLBlock = {"": ""}
    gblMVRStr = ""
    gblGOTOLst = []
    gblEndBlockLst = []
    gblIndent = ""
    gblInLineDeclare = []
    gblParams = {"": []}
    OnConditinalLine:bool = False
    _conditinalLine:str = ""
    _conditinalBlockIndent:int = -1

    def __init__(self, dkey, dsql, lstGoto, params):
        self.gblKeys = dkey
        self.gblSQLBlock = dsql
        self.gblGOTOLst = lstGoto
        self.gblParams = params

    # /////////////////////////////////////////////////////////////////////////
    def cLineBreaker(self, line:str):
        # RPG C line format
        # CL0N01Factor1+++++++Opcode&ExtFactor2+++++++Result++++++++Len++D+HiLoE
        # cann                 z-add     .050          rate              4 3
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
                self.gblEndBlockLst.append("endif;")
                if L0 == "":
                    if N == "":
                        return ["IF", "*in{0} = *On".format(iO1)]
                    else:
                        return ["IF", "*in{0} = *Off".format(iO1)]
                else:
                    return ["IF", "*in{0} = *On".format(L0)]
            else:
                self.gblEndBlockLst.append("endfor;")
                if fact2 != "" and result != "":
                    return ["FOR", "{0} to {1}".format(result, fact2)]
                else:
                    return ["FOR", "1 to {1}".format(result, fact2)]

        # assign block type
        if "IF" in Opcode:
            self.gblEndBlockLst.append("endif;")
        else:
            if "DO" in Opcode and Opcode != "DO":
                self.gblEndBlockLst.append("enddo;")
            else:
                if Opcode == "FOR":
                    self.gblEndBlockLst.append("endfor;")

        # handl lines that dont use factor 1 and 2
        if "EVAL" in Opcode or Opcode == "IF" or Opcode == "FOR" or Opcode == "DOW" or Opcode == "DOU" or Opcode == "WHEN" or Opcode == "RETURN":
            return [Opcode, lin[30:75].strip()]


        #-------------------------------------------------------------------------------------------------
        # remove subroutine (SR) symbol on LO
        # this is legacy code form RPG2
        if L0 == "SR":
            L0 = ""

        # set up if statment for control line
        if N != "" or iO1 != "":
            print(" ------ {0}".format(line))
            self.OnConditinalLine = True
            if L0 == "":
                setLineControl = "IF *in{0} = {1};".format(iO1, controlNtoConst)
            else:
                if L0 == "AN" or L0 == "OR":
                    if L0 == "AN":
                        setLineControl = "And"
                    else:
                        setLineControl = "Or"
                else:
                    setLineControl = "If"
                    
                if N != "":
                    setLineControl = "{0} *in{1} = {2} ".format(setLineControl, iO1, controlNtoConst)
                else:
                    setLineControl = "{0} *in{1} = {2} ".format(setLineControl, iO1, controlNtoConst)
                

        # handle inline declaration
        if Len != "" or d != "":
            if (result in self.gblInLineDeclare) == False:
                # save varialbe name to prevent redeclaration
                self.gblInLineDeclare.append(result)

                # add varialbe declaration to data division
                if Len != "" and d != "":
                    self.gblDataDivision += "Dcl-s {0} zoned({1}: {2});\n".format(result, Len, d)
                else:
                    self.gblDataDivision += "Dcl-s {0} char({1});\n".format(result, Len)

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
    def cComposer(self, originalLine:str) -> str:
        itmArr = self.cLineBreaker(originalLine)
        
        doAddIndent:bool = False
        doIgnoreIndent:bool = False
        isSingleConditinalLine:bool = False
        doTempUnIndent:bool = False
        localIndent:str = ""
        outputLine:str = ""
        tInt:int =0

        #print(itmArr)

        # notihing to compose
        if itmArr is None:
            return ""
        if len(itmArr) == 0:
            return ""
        if "/SPACE" in originalLine:
            return ""    

        # arry contains a RPG line 
        if len(itmArr) == 1:
            return itmArr[0]

        # On conditinal Line
        if self.OnConditinalLine == True:
            self._conditinalLine += itmArr[0]
            isSingleConditinalLine = (self.onBlock(itmArr[0]) == False)

            # check if next item is a conditinal
            if isSingleConditinalLine == True:
                itmArr = itmArr[1:]

                if " GOTO " in originalLine:
                    self.OnConditinalLine = False
                    outputLine = "{0}{1}\n{2}\n{0}endif;\n".format(self.gblIndent, self._conditinalLine, originalLine)
                    self._conditinalLine = ""
                    return outputLine
            
            else:
                return ""

        # set block conditinal line indent
        if self.onBlock(itmArr[0]) == True or self._conditinalLine == True:
            doAddIndent = True
            self._conditinalBlockIndent = (len(self.gblIndent) / 4) + 4

        #print("------------------------------\n{0}\n-----------------------------".format(itmArr))

        # These op codes have already been processed in setup()
        if itmArr[0] == "KLIST" or itmArr[0] == "KFLD" or itmArr[0] == "PLIST" or itmArr[0] == "PARM":
            return ""

        #[Opcode, result, fact1, fact2, hi, lo, eq]
        # comment out compiller directive
        if itmArr[0] == "GOTO" or itmArr[0] == "TAG":
            return "{0}\n".format(originalLine)
        if itmArr[0] == "END":
            return self.normalize_Generic_End_Op(originalLine)


        # on sql operation
        if originalLine[1] == '~':
            outputLine = self.gblSQLBlock[originalLine[1:].strip()] + "\n"
        if itmArr[0] == "MVR":
            outputLine += self.mvr_To_BIF(itmArr[1])
        if itmArr[0] == "LEAVESR":
            outputLine += "return;\n"
        if itmArr[0] == "LEAVE":
            outputLine += "leave;\n"
        if itmArr[0] == "CLEAR":
            outputLine += "clear {0};\n".format(itmArr[1])
        if itmArr[0] == "WHENEQ" or itmArr[0] == "WHENNE" or itmArr[0] == "WHENLE" or itmArr[0] == "WHEGE" or itmArr[0] == "WHENLT" or itmArr[0] == "WHENGT":
            outputLine += "when {0} {1} {2};\n".format(itmArr[2], self.get_RPG3_Comparison_Op(itmArr[0]), itmArr[3])
        if itmArr[0] == "SCAN":
            outputLine += self.nomalize_Scan(itmArr[1], itmArr[2], itmArr[3])
        if itmArr[0] == "EXFMT":
            outputLine += "ExFmt {0};\n".format(itmArr[3])
        if itmArr[0] == "BITOFF":
            outputLine += "{0} = %Bitand({0}: %Bitnot({1}));".format(itmArr[1], itmArr[3])
        if itmArr[0] == "BITON":
            outputLine += "{0} = %Bitor({0}: {1});".format(itmArr[1], itmArr[3])
        if itmArr[0] == "TESTB":
            outputLine += self.normalize_TestB(itmArr[1], itmArr[3], itmArr[4], itmArr[5], itmArr[6])
        if itmArr[0] == "ANDEQ" or itmArr[0] == "ANDNE" or itmArr[0] == "ANDLT" or itmArr[0] == "ANDLE" or itmArr[0] == "ANDGT" or itmArr[0] == "ANDGE":
            outputLine += "and {0} {2} {1} // this is apart of the if/loop block\n".format(itmArr[2], itmArr[3], self.get_RPG3_Comparison_Op(itmArr[0]))
        if itmArr[0] == "OREQ" or itmArr[0] == "ORNE" or itmArr[0] == "ORLT" or itmArr[0] == "ORLE" or itmArr[0] == "ORGT" or itmArr[0] == "ORGE":
            outputLine += "or {0} {2} {1} // this is apart of the if/loop block\n".format(itmArr[2], itmArr[3], self.get_RPG3_Comparison_Op(itmArr[0]))
        if itmArr[0] == "SUBDUR" or itmArr[0] == "ADDDUR":
            outputLine += self.sub_Add_Dur_Translate(itmArr[0], itmArr[2], itmArr[3], itmArr[1])
        if itmArr[0] == "CAT":
            outputLine += "{0} = {1} + {2};\n".format(itmArr[1], itmArr[2], itmArr[3])
        if "OCCUR" in itmArr[0]:
            outputLine += self.normalize_Occur_Op(itmArr[1], itmArr[2], itmArr[3], itmArr[5])
        if "MOVEA" in itmArr[0]:
            outputLine += self.normlaizeMoveA(itmArr[1], itmArr[3])
        if "COMP" in itmArr[0]:
            indResult = self.translate_Indicators(itmArr[4],itmArr[5],itmArr[6])
            outputLine += "*in{0} = ({1} {3} {2});\n".format(indResult[0], itmArr[2], itmArr[3], indResult[1])
        if "Z-ADD" in itmArr[0] or itmArr[0] == "MOVE":
            outputLine += "{0} = {1};\n".format(itmArr[1], itmArr[3])
        if "Z-SUB" in itmArr[0]:
            outputLine += "{0} = (-1 * {1});\n".format(itmArr[1], itmArr[3])
        if itmArr[0] == "ADD" or itmArr[0] == "SUB" or itmArr[0] == "DIV" or itmArr[0] == "MULT" or itmArr[0] == "ADD(H)" or itmArr[0] == "SUB(H)" or itmArr[0] == "DIV(H)" or itmArr[0] == "MULT(H)":
            outputLine += self.math_Operation(itmArr[0], itmArr[2], itmArr[3], itmArr[1], itmArr[4], itmArr[5],itmArr[6])
        if itmArr[0] == "MOVEL":
            outputLine += "// MOVEL Operation: check type before adding spaces/zeros\n{0} {1} = {2}\n".format(itmArr[0], itmArr[1], itmArr[3])
        if itmArr[0] == "EXSR":
            outputLine += "{0}();\n".format(itmArr[3])
        if itmArr[0] == "SETON" or itmArr[0] == "SETOFF":
            outputLine += self.setInd_On_Off(itmArr)
        if itmArr[0] == "EXCEPT":
            outputLine += "write {0}; // write to report format\n".format(itmArr[3])
        if itmArr[0] == "CLOSE" or itmArr[0] == "OPEN":
            outputLine += "{0} {1};\n".format(itmArr[0], itmArr[3])
        if itmArr[0] == "CALL"  or itmArr[0] == "CALLP":
            outputLine += "{0} // call to external procedure or program\n".format(self.get_External_Proc_Call(itmArr[3]))
        if itmArr[0] == "WRITE" or itmArr[0] == "UPDATE" or itmArr[0] == "DELETE":
            outputLine += self.normalize_Write_Update_Delete(itmArr[0], itmArr[3], itmArr[4], itmArr[5])
        if "EVAL" in itmArr[0]:
            outputLine += "{0};\n".format(itmArr[1])
        if itmArr[0] == "RETURN":
            outputLine += self.normlaizeReturn(itmArr[1])
        if "READ" in itmArr[0] or itmArr[0] == "READE" or itmArr[0] == "READC" or itmArr[0] == "READPE":
            outputLine += self.normalize_Read_Op(itmArr[0], itmArr[2], itmArr[3], itmArr[5], itmArr[6])
        if itmArr[0] == "ELSE":
            outputLine += "{0};\n".format(itmArr[0])
        if itmArr[0] == "IF" or itmArr[0] == "FOR" or itmArr[0] == "DOW" or itmArr[0] == "DOU" or itmArr[0] == "WHEN":
            outputLine += "{0} {1};\n".format(itmArr[0], itmArr[1])
        if (itmArr[0])[:2] == "IF" and len(itmArr[0]) > 2:
            outputLine += self.normalize_RPG3_If(itmArr[0], itmArr[2], itmArr[3])
            doAddIndent = True
        if "DOW" in itmArr[0] and itmArr[0] != "DOW":
            outputLine += self.normalize_RPG3_Dow(itmArr[0], itmArr[2], itmArr[3])
            doAddIndent = True
        if "DOU" in itmArr[0] and itmArr[0] != "DOU":
            outputLine += self.normalize_RPG3_Dou(itmArr[0], itmArr[2], itmArr[3])
            doAddIndent = True
        if itmArr[0] == "ENDIF" or itmArr[0] == "ENDDO" or itmArr[0] == "ENDFOR" or itmArr[0] == "ENDSL" or itmArr[0] == "SELECT" or itmArr[0] == "OTHER":
            outputLine += "{0};\n".format(itmArr[0])
            if (itmArr[0] != "SELECT" or itmArr[0] != "OTHER") and len(self.gblEndBlockLst) > 0:
                self.gblEndBlockLst.pop(len(self.gblEndBlockLst)-1)
        if "CHAIN" in itmArr[0]:
            outputLine += self.normalize_File_Find(itmArr[0], itmArr[2], itmArr[3], itmArr[4], itmArr[5])
        if "SETLL" in itmArr[0]:
            outputLine += self.normalize_File_Find(itmArr[0], itmArr[2], itmArr[3], itmArr[4], itmArr[5])
        if "SETGT" in itmArr[0]:
            outputLine += self.normalize_File_Find(itmArr[0], itmArr[2], itmArr[3], itmArr[4], itmArr[5])
        if "CAB" in itmArr[0] and len(itmArr[0]) == 5:
            outputLine += self.namalzie_CAB_Call(itmArr[0], itmArr[2], itmArr[3], itmArr[1])
        if itmArr[0] == "XFOOT":
            outputLine += "{0} = %xfoot({1});\n".format(itmArr[1],itmArr[3])
        if itmArr[0] == "XLATE":
            outputLine += "{0} = %xlate({1}: {2});\n".format(itmArr[1], itmArr[2], itmArr[3])
        if itmArr[0] == "TIME" or itmArr[0] == "DATE":
            outputLine += "{1} = %{0}();\n".format(itmArr[0], itmArr[1])
        if "LOOKUP" in itmArr[0]:
            outputLine += self.normalize_Lookup(itmArr[0], itmArr[2], itmArr[3], itmArr[1], itmArr[6])
        if itmArr[0] == "BEGSR":
            doAddIndent = True
            outputLine += "// /////////////////////////////////////////////////////////////////////////\nDcl-Proc {0};\n".format(itmArr[2])
        if itmArr[0] == "ENDSR":
            outputLine += "End-Proc;\n"
        if itmArr[0] == "SORTA":
            outputLine += "SortA {0};\n".format(itmArr[3])
        if "TEST" in itmArr[0]:
            outputLine += self.normalize_Test_Op(itmArr[0], itmArr[1], itmArr[2], itmArr[5])
        if itmArr[0] == "DSPLY":
            outputLine += "Dsply {0}\n".format(itmArr[2])
            
        # on a standard conditinal line that controls only one line
        if self.OnConditinalLine == True and isSingleConditinalLine == True:
            print("[{0}]".format(self._conditinalLine))
            outputLine = "{1}{0}\n    {1}{2}{1}EndIf;\n".format(self._conditinalLine, self.gblIndent, outputLine)
            self.OnConditinalLine = False
            self._conditinalLine = ""
            return outputLine


        # remove indent
        if "END" == (itmArr[0])[:3]:
            self.gblIndent = self.gblIndent[4:]
            self._conditinalBlockIndent -= 4

            return "{0}{1}".format(self.gblIndent, outputLine)
        
        # at the end of conditinal line that controls a block
        tInt:int =self._conditinalBlockIndent
        if tInt <= 0:
            if tInt == 0:
                self.gblIndent = self.gblIndent[4:]
                outputLine += "{1}{0}endif;\n".format(outputLine, self.gblIndent)
                self._conditinalBlockIndent = -1
                return outputLine
            else:
                self._conditinalBlockIndent = -1
                

        # unable to compose line return original RPG line
        if outputLine.strip == "":
            # nothing to do just print the line
            outputLine = originalLine + "\n"
        else:
            # if needed adjust the indent
            if self.specialBlockKeywords(itmArr[0]) == True:
                localIndent = self.gblIndent[4:]
            else:
                localIndent = self.gblIndent

            # add Indent when needed
            outputLine = localIndent + outputLine

        # add indent
        if doAddIndent == True:
            self.gblIndent += "    "
            doAddIndent = False

        #print(outputLine.rstrip())
        return outputLine


    # /////////////////////////////////////////////////////////////////////////
    def normalize_Occur_Op(self, result, fact1, fact2, lo):
        self.gblIndent
        ret = ""
        
        # determin the occurance operation (get/set)
        if fact1 == "":
            ret += "{0} = %Occur({1}); // GET occurrence index\n".format(result, fact2)
        else:
            ret += "%Occur({1}) = {0}; // SET occurrence index\n".format(fact1, fact2)

        # process occurance indicator
        if lo != "":
            ret += "{1}*in{0} = %Error();\n".format(lo, self.gblIndent)

        return ret
        
    # /////////////////////////////////////////////////////////////////////////
    def normalize_Read_Op(self, op, fact1, fact2, lo, eq): 
        self.gblIndent
        ret = ""

        # process read operation
        if fact1 == "":
            ret += "{0} {1};\n".format(op, fact2)
        else:
            ret += "{0} {1} {2};\n".format(op, self.get_Key_String(fact1), fact2)
            
        # process indicators
        if lo != "":
            ret += "{1}*in{0} = %error();\n".format(lo, self.gblIndent)
        if eq != "":
            ret += "{1}*in{0} = %eof();\n".format(eq, self.gblIndent)

        return ret

    # /////////////////////////////////////////////////////////////////////////
    def normalize_Test_Op(self, op, result, fact1, lo):
        tsOp = {"TEST(D)":"Test(DE)",  # date error
                "TEST(Z)":"Test(ZE)",  # timestamp error
                "TEST(T)":"Test(TE)",  # time error
                "TEST(DE)":"Test(DE)",
                "TEST(TE)":"Test(TE)",
                "TEST(ZE)":"Test(ZE)"}

        # normalize op by removeing spaces
        op = op.replace(" ", "")

        # translate op to freeformat op
        if op in tsOp:
            freeOp = tsOp[op]
        else:
            return ""
        
        # rewrite line
        ret = "{0} {1} {2};\n".format(freeOp, fact1, result)

        # apply indicator
        if lo != "":
            ret += "{0}*in{1} = %error();\n".format(self.gblIndent, lo)

        return ret

    # /////////////////////////////////////////////////////////////////////////
    def normalize_Generic_End_Op(self, originalLine):
        # remove indent
        self.gblIndent = self.gblIndent[4:]

        # get the current block type
        if len(self.gblEndBlockLst) == 0:
            return "{0}\n".format(originalLine)
        else:
            return "{0}{1}\n".format(self.gblIndent, self.gblEndBlockLst.pop(len(self.gblEndBlockLst)-1))

    # /////////////////////////////////////////////////////////////////////////
    def setInd_On_Off(self, arr):
        cnt = 0
        tstr = ""
        ret = ""

        # convert seton/setoff to freeform assignment
        # array element 0 is the opcode 
        for ind in arr[1:]:
            if ind != "":
                if "ON" in arr[0]:
                    tstr = "*in{0} = *On;\n".format(ind, self.gblIndent)
                else:
                    tstr = "*in{0} = *Off;\n".format(ind, self.gblIndent)

                # setup indents
                # skip the first as it will be indented in composer
                if cnt > 0:
                    ret += self.gblIndent + tstr
                else:
                    ret += tstr
                cnt += 1
        
        return ret

    # /////////////////////////////////////////////////////////////////////////
    def mvr_To_BIF(self, result):
        return  "{0} = {1}".format(result, self.gblMVRStr)
        
    # /////////////////////////////////////////////////////////////////////////
    def math_Operation(self, op, fact1, fact2, result, HI, LO, EQ):
        oper = {"DIV":"/", "MULT":"*", "ADD":"+", "SUB":"-",
                "DIV(H)":"/", "MULT(H)":"*", "ADD(H)":"+", "SUB(H)":"-"}
        ret = ""

        if fact1 != "":
            ret += "{0} = {1} {2} {3};\n".format(result, fact1, oper[op], fact2)
        else:
            ret += "{0} {1}= {2};\n".format(result, oper[op], fact2)

        if HI != "":
            ret += "*in{0} = ({1} > 0);\n".format(HI, result)
        if LO != "":
            ret += "*in{0} = ({1} < 0);\n".format(LO, result)
        if EQ != "":
            ret += "*in{0} =({1} = 0);\n".format(EQ, result)

        # assign MVR value
        if op == "DIV":
            if fact1 != "":
                self.gblMVRStr = "%rem({0}: {1});\n".format(fact1, fact2)
            else:
                self.gblMVRStr = "%rem({0}: {1});\n".format(result, fact2)

        # return new freeformat math operaton
        return ret

    # /////////////////////////////////////////////////////////////////////////
    def sub_Add_Dur_Translate(self, op, fact1, fact2, result):
        durationToFunc = {"*YEARS"   : "years"   , "*Y" : "years"   , 
                        "*MONTHS"  : "months"  , "*M" : "months"  , 
                        "*DAYS"    : "Days"    , "*D" : "Days"    , 
                        "*HOURS"   : "Hours"   , "*H" : "Hours"   , 
                        "*MINUTES" : "minutes" , "*MN": "minutes" , 
                        "*SECONDS" : "Seconds" , "*S" : "Seconds" , 
                        "*MSECONDS": "mseconds", "*MS": "mseconds" }
        mathOp = ""

        # generate assignment operation
        if "ADD" in op:
            mathOp = "+="
        else:
            mathOp = "-="

        # get the factor that has a [:] 
        if ":" in fact2:
            # on factor 2 operation returns a date
            arr = fact2.split(":")
            return "{0} {3} %{1}({2});\n".format(result, durationToFunc[arr[1]], arr[0], mathOp)
        else:
            #on result operation returns an integer
            arr = result.split(":")
            return "{0} = %diff({1}:{2}:{3});\n".format(arr[0], fact1, fact2, arr[1])

    # /////////////////////////////////////////////////////////////////////////
    def translate_Indicators(self, hi, lo, eq):
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
    def normalize_Lookup(self, Opcode, fact1, fact2, result, eq):
        tarr = []
        ind = ""
        arrOrTable = ""

        # remove array indexing in fact2
        # this is done by converting fact2 int a array [TArr]
        # TArr[0] = arrayName
        # TArr[1] = indexFoundAt
        if "(" in fact2:
            arrOrTable = fact2.replace(")","")
            tarr = arrOrTable.split("(")
            arrOrTable = tarr[0]
            
        if len(tarr) == 2:
            ind = "{0}*in{1} = ({2} <> 0);".format(self.gblIndent, eq, tarr[1])
        else:
            return "*in{0} = %{3}({1}: {2});\n".format(eq, fact1, fact2, Opcode)

        return "{0} = %{4}({1}: {2});\n{3}\n".format(tarr[1], fact1, arrOrTable, ind, Opcode)

    # /////////////////////////////////////////////////////////////////////////
    def namalzie_CAB_Call(self, Opcode, fact1, fact2, result):
        # setup comparison form cab opcode
        compar = self.get_RPG3_Comparison_Op(Opcode)
        msg = "();"

        # result of cab is a GOTO so flag it
        if result in self.gblGOTOLst:
            msg = " // goto this tag"

        return "IF {0} {2} {1};\n{4}    {3}{5}\n{4}ENDIF;\n".format(fact1, fact2, compar, result, self.gblIndent, msg)

    # /////////////////////////////////////////////////////////////////////////
    def get_RPG3_Comparison_Op(self, op):
        drez = {"EQ":"=", "NE":"<>","LT":"<","LE":"<=","GT":">","GE":">="}

        if len(op) > 2:
            operand = op[len(op)-2:]
        else:
            operand = op

        if operand in drez:
            return drez[operand]

        return ""

    # /////////////////////////////////////////////////////////////////////////
    def get_Key_String(self, keyName):
        ret = ""

        if keyName in self.gblKeys:
            arr = self.gblKeys[keyName]

            for i in range(len(arr)):
                if i > 0:
                    if i < (len(arr) - 1):
                        ret += arr[i] + ": "
                    else:
                        ret += arr[i]
            return "(" + ret + ")"
        
        return "(" + keyName + ")"
        
    # /////////////////////////////////////////////////////////////////////////
    def getCallParamList(self, callName):
        ret = ""

        # check if call is in paramiter dicationary
        if callName in self.gblParams:
            arr = self.gblParams[callName]

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
    def get_External_Proc_Call(self, procName):
        name = procName.replace("'","")

        lst = self.getCallParamList(name)

        return "{0}{1};".format(name, lst)

    # /////////////////////////////////////////////////////////////////////////
    def normalize_RPG3_If(self, op, fact1, fact2):
        logicalOP = self.get_RPG3_Comparison_Op(op)

        return "If {0} {1} {2};\n".format(fact1, logicalOP, fact2)

    # /////////////////////////////////////////////////////////////////////////
    def normalize_RPG3_Dow(self, op, fact1, fact2):
        logicalOP = self.get_RPG3_Comparison_Op(op)

        return "Dow {0} {1} {2};\n".format(fact1, logicalOP, fact2)

    # /////////////////////////////////////////////////////////////////////////
    def normalize_RPG3_Dou(self, op, fact1, fact2):
        logicalOP = self.get_RPG3_Comparison_Op(op)

        return "Dou {0} {1} {2};\n".format(fact1, logicalOP, fact2)

    # /////////////////////////////////////////////////////////////////////////
    def normalize_File_Find(self, op, fact1, fact2, hi, lo):
        ret = ""

        ret = "{0} {1} {2};\n".format(op, self.get_Key_String(fact1), fact2)

        if hi != "":
            ret += "{1}*in{0} = (%found() = *Off);\n".format(hi, self.gblIndent)
        if lo != "":
            ret += "{1}*in{0} = %error();\n".format(lo, self.gblIndent)
        
        return ret

    # /////////////////////////////////////////////////////////////////////////
    def normalize_Write_Update_Delete(self, op, fact2, hi, lo):
        ret = ""

        ret += "{0} {1};\n".format(op, fact2)

        if hi != "":
            ret += "{1}*in{0} = %error();\n".format(hi, self.gblIndent)
        if lo != "":
            ret += "{1}*in{0} = %eof();\n".format(lo, self.gblIndent)

        return ret

    # /////////////////////////////////////////////////////////////////////////
    def normalize_TestB(self, result, fact2, hi, lo, eq):
        ret = ""
    
        if hi != "":
            ret += "*in{2} = %Bitand({0}: {1}) = x'00';\n".format(result, fact2, hi)
        else:
            if eq != "":
                ret += "*in{2} = %Bitand({0}: {1}) = {1};\n".format(result, fact2, eq)
            else:
                ret += "*in{2} = %Bitand({0}: {1}) <> x'00' and  %Bitand({0}: {1}) <> {1};\n".format(result, fact2, lo)
        
        return ret

    # /////////////////////////////////////////////////////////////////////////
    def nomalize_Scan(self, result, fact1, fact2):
        ret = ""

        #[Opcode, result, fact1, fact2, hi, lo, eq]
        if len(result) == 0:
            ret += "%Scan({0}: {1}));  // use %found() to check if string was found\n".format(fact1, fact2)
        else:
            ret += "{2} = %Scan({0}: {1});\n".format(fact1, fact2, result)
        return ret

    # /////////////////////////////////////////////////////////////////////////
    def normlaizeReturn(self, fact2):
        if len(fact2) == 0:
            return "Return;\n"
        else:
            return "Return {0};\n".format(fact2)
            
    # /////////////////////////////////////////////////////////////////////////
    def normlaizeMoveA(self, result, fact2):
        indic:str
        outstr:str
        strval:str
        count:int
        indnum:int
        indent:str

        if result[:4] == "*IN(":
            indic = (result.split("("))[1]
            indic = indic.replace(")","")
            indnum = int(indic)
            strval = fact2.replace("'","")

            count = 0
            outstr = ""
            indent = ""

            for chr in strval:
                if count > 0:
                    indent = self.gblIndent

                if chr == "0":
                    outstr += "{1}*in{0} = *Off;\n".format(indnum, indent)
                else:
                    outstr +=  "{1}*in{0} = *On;\n".format(indnum, indent)

                count += 1
                indnum += 1

            return outstr
        else:
            return "{0} = {1};\n".format(result, fact2)

    # /////////////////////////////////////////////////////////////////////////
    def addIndent(self):
        self.gblIndent += "    "
        
    # /////////////////////////////////////////////////////////////////////////
    def removeIndent(self):
        self.gblIndent = self.gblIndent[4:]
            
    # /////////////////////////////////////////////////////////////////////////
    def getDataDivision(self):
        return self.gblDataDivision
    
    # /////////////////////////////////////////////////////////////////////////
    def onBlock(sefl, kwrd:str) -> bool:
        if kwrd == "IF" or kwrd == "FOR" or kwrd == "DOW" or kwrd == "DOU" or kwrd == "SELECT" or kwrd == "DO":
            return True
        return False

    # /////////////////////////////////////////////////////////////////////////
    def specialBlockKeywords(self, kwrd:str) -> bool:
        if kwrd == "WHEN" or kwrd == "ELSE":
            return True
        return False

    # /////////////////////////////////////////////////////////////////////////
    def getIndent(self):
        return self.gblIndent
