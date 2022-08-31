class H_Composer:
    gblFileDivision = ""

    def Hcomposer(self, line):
        self.gblFileDivision += "Ctl-Opt " + line[1:].strip() + ";\n"