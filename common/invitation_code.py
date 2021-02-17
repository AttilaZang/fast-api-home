from random import choice

chars = [
    "9", "W", "6", "U", "X", "e", "7", "g", "S", "2", "R",
    "J", "8", "P", "5", "a", "3", "M", "Z", "F", "C", "4",
    "b", "N", "h", "L", "Y", "q", "K", "V", "T"
]

# 因为有的邀请码是不足6位的，所以要有间隔码, 间隔码不能再chars中
DIVIDER = "D"
# // 最短设备码
CODE_MIN_LENGTH = 6

def id2code(id):
    buf = ''

    # 将10进制的id转化为33进制的邀请码
    while (id / len(chars)) > 0:
        index = id % len(chars)
        buf += chars[index]
        id = int(id / len(chars))
    buf += chars[int(id % len(chars))]

    # 翻转buf字符串
    buf = buf[::-1]

    # 补充长度
    fixLen = CODE_MIN_LENGTH - len(buf)
    if fixLen > 0:
        buf += DIVIDER

        i = 0
        while i < (fixLen - 1):
            buf += choice(chars)
            i += 1

    return buf


def code2id(code):
    codeLen = len(code)
    id = 0

    # 33进制转10进制
    i = 0
    while i < codeLen:
        if str(code[i]) == DIVIDER:
            break

        index, j = 0, 0
        while j < len(chars):
            if str(code[i]) == chars[j]:
                index = j
                break
            j += 1

        if i > 0:
            id = id * len(chars) + index
        else:
            id = index

        i += 1
    return id


if __name__ == '__main__':
    code_10 = id2code(10)
    print(code_10)

    # # print('=============')
    id10 = code2id(code_10)   # 这个反解析有问题，随便输入也能解析
    print(id10, type(id10))

