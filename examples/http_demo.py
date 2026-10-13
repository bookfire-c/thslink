"""ThsLink-Cli（纯接口版） HTTP 示例。安装依赖 pip install requests。
直接运行只查询连接和账户，不提交交易。业务程序显式调用 order / batch。
v0.2.6 起交易必须 notip=True；本示例自动补齐，显式传入其他值会在发送前报错。
"""
import atexit
import requests

BASE = "http://127.0.0.1:8421"
HEADERS = {}  # 配置密钥时填写 {"X-API-Key": "你的密钥"}
# 只初始化一次。下单、查询和轮询共用此客户端；多线程请每线程各保留一个。
SESSION = requests.Session()
atexit.register(SESSION.close)


def get(path):
    response = SESSION.get(BASE + path, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.json()


def post(path, payload):
    response = SESSION.post(BASE + path, json=payload, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def _trading_payload(payload):
    """补齐必填参数；拒绝其他值，不改动调用方的字典。"""
    payload = dict(payload)
    payload.setdefault("notip", True)
    if payload["notip"] is not True:
        raise ValueError("交易请求必须填写 notip=True，本次未发送")
    return payload


def order(side, code, price=None, amount=None, **flags):
    payload = {"side": side, "code": code}
    if price is not None:
        payload["price"] = str(price)
    if amount is not None:
        payload["amount"] = amount
    payload.update(flags)
    return post("/order", _trading_payload(payload))


def buy(code, price="mrxjg", amount=None, **flags):
    if amount is None and not any(key in flags for key in ("m", "cw", "zzc", "zcw")):
        amount = 100
    return order("buy", code, price, amount, **flags)


def sell(code, price="mcxjg", amount=None, **flags):
    if amount is None and not any(key in flags for key in ("m", "cw", "zzc", "zcw")):
        amount = 100
    return order("sell", code, price, amount, **flags)


def cancel(code="all", **flags):
    return order("cancel", code, **flags)


def cancel_all(**flags):
    return cancel("all", **flags)


def batch(orders):
    """一次提交 1～20 笔；逐笔补齐 notip=True，任一笔无效则整批未发送。"""
    payloads = [_trading_payload(order) for order in orders]
    return post("/orders/batch", {"orders": payloads})


def order_result(request_id):
    return get(f"/orders/{request_id}")


def batch_result(batch_id):
    return get(f"/batches/{batch_id}")


def query(kind, account="current", wait_ms=2000):
    """主动查询：holdings / orders / deals / funds；pending 时查原 query_id。"""
    return post("/query", {"kind": kind, "account": account, "wait_ms": wait_ms})


def query_result(query_id):
    return get(f"/queries/{query_id}")


def check_health():
    return get("/health")


def who():
    return get("/who")


def last():
    """最新回执仅供诊断，不代替按编号查询。"""
    return get("/last")


# 业务程序按需调用（实际交易）：
# result = batch([
#     {"side":"buy","code":"000009","price":"mrxjg","amount":100,"notip":True},
#     {"side":"buy","code":"600000","price":"mrxjg","cw":"1/10","notip":True},
# ])
# print(batch_result(result["batch_id"]))
# 等待中继续查询原编号，勿直接重发；需要归档的日志由调用程序保存。

if __name__ == "__main__":
    print(check_health())
    print(who())
