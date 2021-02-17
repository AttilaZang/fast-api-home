# 400Error Object
class Request400Error(Exception):
    def __init__(self, error_msg):
        self.error_msg = error_msg


# 403Error Object
class Request403Error(Exception):
    def __init__(self, error_msg):
        self.error_msg = error_msg


# 404Error Object
class Request404Error(Exception):
    def __init__(self, error_msg):
        self.error_msg = error_msg


# 500Error Object
class Request500Error(Exception):
    def __init__(self, error_msg):
        self.error_msg = error_msg

