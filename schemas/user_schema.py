from pydantic import BaseModel, Field
from utils.constants import AVATAR


class GoodsMsg(BaseModel):
    """取货信息"""
    user_id: int
    get_addr: str
    recv_addr: str
    contacts: str
    mobile: str
    weight: str
    take_info: str
    lng: float  # 取货地址的经度
    lat: float  # 取货地址的纬度
    cost: int  # 用完券之后的
    out_trade_no: str  # 支付单号
    gender: int  # 性别
    coupons_id: int = -1  # -1 代表未传coupons_id


class BindMobile(BaseModel):
    user_id: int
    encryptedData: str
    iv: str
    code: str


class Login(BaseModel):
    js_code: str


class User(BaseModel):
    id: int
    name: str
    mobile: str
    is_courier: bool = False
    avatar: str = AVATAR

    class Config:
        orm_mode = True


class TokenUser(User):
    token: str = ''


class UserEdit(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(max_length=16, min_length=2)


class AddrCreate(BaseModel):
    user_id: int = Field(gt=0)
    contacts: str  # 联系人
    gender: int
    mobile: str
    place: str
    addr_type: str
    lng: float
    lat: float
    region: str


class AddrDelete(BaseModel):
    id: int


class AddrUpdate(AddrCreate, AddrDelete):
    pass


class Order(BaseModel):
    id: int
    order_num: str
    recv_addr: str
    take_info: str
    status: int

    class Config:
        orm_mode = True


class Comment(BaseModel):
    order_id: int
    score: int
    is_anonymous: bool = True


class WxPay(BaseModel):
    user_id: int
    good_price: int


class WxRefund(BaseModel):
    total_fee: int
    out_refund_no: str
