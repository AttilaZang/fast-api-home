

def printBlue(text):
    return "\033[%sm%s\033[0m" % ('34', text)

def printRed(text):
    return "\033[%sm%s\033[0m" % ('31', text)

def printGreen(text):
    return "\033[%sm%s\033[0m" % ('32', text)

def printYellow(text):
    return "\033[%sm%s\033[0m" % ('33', text)


