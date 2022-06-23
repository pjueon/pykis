import os, sys

# sys.path에 상위 디렉토리 추가
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import pykis
import json
# import official_sample as sample

# key 정보
with open("keys/key.json", "r") as f:
    keys = json.load(f)

print("keys.json load...")
print(f"keys: {keys}")


api = pykis.Api(**keys)
print("api 객체 생성 완료")

# print(f"api.need_auth(): {api.need_auth()}")
# print("try to auth...")

# api.auth()
# print(f"auth done. api.need_auth(): {api.need_auth()}")

# p = {
#     "ORD_PRCS_DVSN_CD": "02",
#     "CANO": "계좌번호",
#     "ACNT_PRDT_CD": "03",
#     "SLL_BUY_DVSN_CD": "02",
#     "SHTN_PDNO": "101S06",
#     "ORD_QTY": "1",
#     "UNIT_PRICE": "370",
#     "NMPR_TYPE_CD": "",
#     "KRX_NMPR_CNDT_CD": "",
#     "CTAC_TLNO": "",
#     "FUOP_ITEM_DVSN_CD": "",
#     "ORD_DVSN_CD": "02"
# }
# k = api.get_hash_key(p)

# print(f"key: {k}")

etf = "411060"
price = api.get_kr_stock_price(ticker=etf)
print(f"current price: {price} krw")
cash = api.get_kr_buyable_cash()
print(f"cash: {cash} krw")

stock = api.get_kr_stock_balance()
print(f"주식: {stock}")

deposit = api.get_kr_deposit()
print(f"예수금: {deposit}")

# ret = api.buy_kr_stock(etf, 1, price=7710)
# print(ret)