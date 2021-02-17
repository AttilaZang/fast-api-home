from pydantic import BaseModel, Field


class VerifyName(BaseModel):
    courier_id: int
    mobile: str
    id_card_front: str
    id_card_back: str
    id_card_hand: str


class CourierRegister(BaseModel):
    mobile: str = Field(..., regex=r'^1[3-9]\d{9}$')
    sms_code: int


class ServiceArea(BaseModel):
    courier_id: int
    service_area: str
    lng: float
    lat: float


class Order(BaseModel):
    id: int
    order_num: str
    recv_addr: str
    take_info: str
    status: int

    class Config:
        orm_mode = True


class AlipayInfo(BaseModel):
    courier_id: int
    name: str
    account: str


class CashOut(BaseModel):
    courier_id: int
    balance: int = Field(ge=5000)


class CashOutRecord(BaseModel):
    courier_id: int
    year: int
    month: int


class CapitalDetail(CashOutRecord):
    pass


class ResetPassword(BaseModel):
    courier_id: int
    pwd: str = Field(min_length=6, max_length=16)
    repwd: str = Field(min_length=6, max_length=16)


class PasswordLogin(BaseModel):
    mobile: str = Field(..., regex=r'^1[3-9]\d{9}$')
    pwd: str = Field(min_length=6, max_length=16)


class StartDelivery(BaseModel):
    order_id: int


class FinishDelivery(StartDelivery):
    courier_id: int


class Transfer(BaseModel):
    """后台完成骑手打款"""
    bill_id: int  # 账单id
    courier_id: int  # 骑手id
    amount: int  # 提现的金额
    self_pwd: str = Field(max_length=16)  # 管理员的密码


class CheckMsg(BaseModel):
    """后台通过骑手实名认证"""
    courier_id: int
    last_name: str  # 骑手真实姓
    first_name: str  # 骑手真实名
    self_pwd: str = Field(max_length=16)  # 管理员的密码


class CourierCheck(BaseModel):
    """后台获取骑手待审核实名认证列表"""
    self_pwd: str = Field(max_length=16)  # 管理员的密码


class CourierTransfer(CourierCheck):
    """后台获取骑手提交提现记录"""


class PaymentAccount(BaseModel):
    courier_id: int
