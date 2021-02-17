
import time
import jwt

SECRET_KEY = '4c94fbca9e0fa8da60195ad5612c8a20a2bb446bb9e2d5deaa5d929356ea03e7'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_DAYS = 30  # 可以不用


def generate_jwt(mobile: str, user_id: int = None, courier_id: int = None):

    key, value = ('user_id', user_id) if user_id else ('courier_id', courier_id)

    payload = {
        key: value,
        'mobile': mobile,
        'unix': time.time()
    }
    encode_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt


if __name__ == '__main__':
    ret = generate_jwt(user_id=1, mobile='')
    print(ret)
    print(jwt.decode(ret, SECRET_KEY, algorithms=[ALGORITHM]))