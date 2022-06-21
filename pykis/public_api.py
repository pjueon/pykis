# Copyright 2022 Jueon Park
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime, timedelta
from collections import namedtuple
from typing import NamedTuple, Optional, Dict, Iterable
import json
import requests

Json = Dict

# request 관련 유틸리티------------------


def merge_json(datas: Iterable[Json]) -> Json:
    """
    여러개의 json 형식 데이터를 하나로 통합하여 반환한다. 
    동일한 key가 있는 경우 뒤에 있는 원소로 덮어쓴다. 
    """
    ret = {}
    for data in datas:
        for key, value in data.items():
            ret[key] = value
    return ret


def to_namedtuple(name: str, json_data: Json) -> NamedTuple:
    """
    json 형식의 데이터를 NamedTuple 타입으로 반환한다.
    """
    _x = namedtuple(name, json_data.keys())
    return _x(**json_data)


def get_base_headers() -> Json:
    """
    api에 사용할 header의 기본 base를 반환한다.   
    """
    base = {
        "Content-Type": "application/json",
        "Accept": "text/plain",
        "charset": "UTF-8",
    }

    return base


def send_get_request(url, headers, params) -> Json:
    """
    HTTP GET method로 request를 보내고 response에서 body.output을 반환한다. 
    """
    resp = requests.get(url, headers=headers, params=params)

    if resp.status_code != 200:
        msg = f"http response code: {resp.status_code}"
        raise RuntimeError(msg)

    body = to_namedtuple("body", resp.json())

    if body.rt_cd != "0":
        msg = f"error message: {body.msg1}, return code: {body.rt_cd}"
        raise RuntimeError(msg)

    return body.output

# request 관련 유틸리티------------------


class DomainInfo:
    def __init__(self, kind: Optional[str] = None, url: Optional[str] = None) -> None:
        if kind == "real":
            self.base_url = "https://openapi.koreainvestment.com:9443"
        elif kind == "virtual":
            self.base_url = "https://openapivts.koreainvestment.com:29443"

        elif kind is None and url is not None:
            self.base_url = url
        else:
            raise RuntimeError("invalid domain info")

    def get_url(self, url_path: str):
        """
        url_path를 입력받아서 전체 url을 반환한다.
        """
        return f"{self.base_url}{url_path}"


class AccessToken:
    def __init__(self, resp: Json) -> None:
        r = to_namedtuple("res", resp)
        time_margin = timedelta(minutes=1)

        self.value = f"Bearer {str(r.access_token)}"
        self.valid_until = datetime.now() + timedelta(seconds=int(r.expires_in)) - time_margin

    def is_valid(self) -> bool:
        """
        access token이 유효한지 검사한다.
        """
        return datetime.now() < self.valid_until


class Api:
    def __init__(self, key_info: Json, domain_info=DomainInfo(kind="real"), account_info: Optional[Json] = None) -> None:
        """
        key_info: API 사용을 위한 인증키 정보. appkey, appsecret
        domain_info: domain 정보 (실전/모의/etc)
        account_info: 사용할 계좌 정보. { "account_code" : "[계좌번호 앞 8자리 숫자]", "product_code" : "[계좌번호 뒤 2자리 숫자]" }
        """
        self.key: Json = key_info
        self.domain: DomainInfo = domain_info
        self.token: Optional[AccessToken] = None
        self.account: Optional[NamedTuple] = None

        if account_info is not None:
            self.set_account(account_info)

    def set_account(self, account_info: Json) -> None:
        """
        사용할 계좌 정보를 설정한다.
        account_info: 사용할 계좌 정보. { "account_code" : "[계좌번호 앞 8자리 숫자]", "product_code" : "[계좌번호 뒤 2자리 숫자]" }
        """
        self.account = to_namedtuple("account", account_info)

    def _send_get_request(self, url_path, tr_id, params) -> Json:
        """
        HTTP GET method로 request를 보내고 response에서 body.output을 반환한다. 
        """
        url = self.domain.get_url(url_path)

        if self.need_auth():
            self.auth()

        headers = merge_json([
            get_base_headers(),
            self.get_api_key_data(),
            {
                "authorization": self.token.value,
                "tr_id": tr_id
            }
        ])

        return send_get_request(url, headers, params)

    # 인증-----------------

    def auth(self) -> None:
        """
        access token을 발급한다.
        """
        url_path = "/oauth2/tokenP"
        url = self.domain.get_url(url_path)

        param = merge_json([
            self.get_api_key_data(),
            {
                "grant_type": "client_credentials"
            }
        ])

        headers = get_base_headers()

        resp = requests.post(url, data=json.dumps(param), headers=headers)

        if resp.status_code != 200:
            raise RuntimeError("Authentication failed")

        self.token = AccessToken(resp.json())

    def need_auth(self) -> bool:
        """
        authentication이 필요한지 여부를 반환한다. 
        """
        return self.token is None or not self.token.is_valid()

    def set_hash_key(self, header: Json, param: Json) -> None:
        """
        header에 hash key 설정한다. 
        """
        hash_key = self.get_hash_key(param)
        header["hashkey"] = hash_key

    def get_hash_key(self, param: Json) -> str:
        """
        hash key 값을 가져온다. 
        """
        url_path = "/uapi/hashkey"
        url = self.domain.get_url(url_path)

        headers = merge_json([get_base_headers(), self.get_api_key_data()])

        resp = requests.post(url, data=json.dumps(param), headers=headers)
        if resp.status_code != 200:
            msg = f"get_has_key failed. response code: {resp.status_code}"
            raise RuntimeError(msg)

        return to_namedtuple("res", resp.json()).HASH

    def get_api_key_data(self) -> Json:
        """
        사용자의 api key 데이터를 반환한다.
        """
        key_data = {
            "appkey": self.key["appkey"],
            "appsecret": self.key["appsecret"]
        }
        return key_data

    # 인증-----------------

    # 시세 조회------------
    def get_kr_stock_price(self, ticker: str) -> int:
        """
        국내 주식 현재가를 반환한다. 
        ticker: 종목코드
        return: 해당 종목 현재가 (단위: 원)
        """
        info = self._get_kr_stock_current_price_info(ticker)
        price = info["stck_prpr"]

        return int(price)

    def _get_kr_stock_current_price_info(self, ticker: str) -> Json:
        """
        국내 주식 현재가 시세 정보를 반환한다.
        ticker: 종목코드
        return: 해당 종목 현재 시세 정보
        """
        url_path = "/uapi/domestic-stock/v1/quotations/inquire-price"

        tr_id = "FHKST01010100"

        params = {
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_INPUT_ISCD': ticker
        }

        return self._send_get_request(url_path, tr_id, params)

    # 시세 조회------------

    # 잔고 조회------------
    def get_kr_buyable_cash(self) -> int:
        """
        구매 가능 현금(원화) 조회
        return: 해당 계좌의 구매 가능한 현금(원화)
        """
        url_path = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
        tr_id = "TTTC8908R"
        url = self.domain.get_url(url_path)

        if self.account is None:
            msg = f"계좌가 설정되지 않았습니다. set_account를 통해 계좌 정보를 설정해주세요."
            raise RuntimeError(msg)

        stock_code = ""
        qry_price = 0

        params = {
            "CANO": self.account.account_code,
            "ACNT_PRDT_CD": self.account.product_code,
            "PDNO": stock_code,
            "ORD_UNPR": str(qry_price),
            "ORD_DVSN": "02",
            "CMA_EVLU_AMT_ICLD_YN": "Y",
            "OVRS_ICLD_YN": "N"
        }

        output = self._send_get_request(url_path, tr_id, params)
        return int(output["ord_psbl_cash"])

    def get_kr_stock_balance(self):
        """
        국내 주식 잔고 조회
        return: 국내 주식 잔고 정보를 DataFrame으로 반환
        """
        return
    # 잔고 조회------------

    # 매매-----------------
    def buy_kr_stock(self, ticker: str, order_amount: int, price: int):
        """
        국내 주식 매수(현금)
        ticker: 종목코드
        order_amount: 주문 수량
        price: 주문 가격
        """
        return

    def sell_kr_stock(self, ticker: str, order_amount: int, price: int):
        """
        국내 주식 매매(현금)
        ticker: 종목코드
        order_amount: 주문 수량
        price: 주문 가격
        """
        return
    # 매매-----------------
