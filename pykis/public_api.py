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
from typing import NamedTuple, Optional, Dict, Iterable, Any, List, Tuple
import json
import requests
import pandas as pd

Json = Dict[str, Any]

# request 관련 유틸리티------------------


class APIResponse:
    def __init__(self, resp: requests.Response) -> None:
        self.http_code: int = resp.status_code
        self.header: Json = self._get_header(resp)
        self.body: Json = resp.json()
        self.message: str = self._get_message()
        self.return_code: Optional[str] = self._get_return_code()
        self.outputs: List[Json] = self._get_outputs()

    def is_ok(self) -> bool:
        """
        아무런 오류가 없는 경우 True, 오류가 있는 경우 False를 반환한다. 
        """
        return self.http_code == 200 and (self.return_code == "0" or self.return_code is None)

    def raise_if_error(self, check_http_error=True, check_return_code=True) -> None:
        """
        오류가 난 경우 예외를 던진다. 
        """
        error_message = f"http response: {self.http_code}, return code: {self.return_code}. msg: {self.message}"

        if check_http_error and self.http_code != 200:
            raise RuntimeError(error_message)

        if check_return_code and self.return_code != "0" and self.return_code is not None:
            raise RuntimeError(error_message)

    def _get_message(self) -> str:
        """
        API의 response에서 응답 메시지를 찾아서 반환한다. 없는 경우 빈 문자열을 반환.
        """
        if "msg" in self.body:
            return self.body["msg"]
        elif "msg1" in self.body:
            return self.body["msg1"]
        else:
            return ""

    def _get_return_code(self) -> Optional[str]:
        """
        API에서 성공/실패를 나타내는 return code를 찾아서 반환한다. 없는 경우 None을 반환
        """
        return self.body.get("rt_cd", None)

    def _get_outputs(self) -> List[Json]:
        """
        API의 output 값(ex> output, output1, output2)들을 list로 가져온다. 
        뒤에 붙은 번호 순서대로(output이 있는 경우 제일 앞) 배치한다.
        """
        target_keys = ["output", "output1", "output2"]
        ret = [self.body[target]
               for target in target_keys if target in self.body]

        return ret

    def _get_header(self, resp: requests.Response) -> Json:
        """
        API의 response에서 header 정보를 찾아서 반환한다. 
        """
        header = dict()
        for x in resp.headers.keys():
            if x.islower():
                header[x] = resp.headers.get(x)
        return header


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


def send_get_request(url: str, headers: Json, params: Json) -> APIResponse:
    """
    HTTP GET method로 request를 보내고 APIResponse 객체를 반환한다. 
    """
    resp = requests.get(url, headers=headers, params=params)
    r = APIResponse(resp)
    r.raise_if_error()

    return r


def send_post_request(url: str, headers: Json, params: Json) -> APIResponse:
    """
    HTTP POST method로 request를 보내고 APIResponse 객체를 반환한다. 
    """
    resp = requests.post(url, headers=headers, data=json.dumps(params))
    r = APIResponse(resp)
    r.raise_if_error()

    return r


# request 관련 유틸리티------------------


class DomainInfo:
    def __init__(self, kind: Optional[str] = None, url: Optional[str] = None) -> None:
        self.kind = kind
        self.base_url = self._get_base_url(url)

    def get_url(self, url_path: str):
        """
        url_path를 입력받아서 전체 url을 반환한다.
        """
        separator = "" if url_path.startswith("/") else "/"
        return f"{self.base_url}{separator}{url_path}"

    def _get_base_url(self, input_url: Optional[str]) -> str:
        """
        domain 정보를 나타내는 base url 반환한다. 잘못된 입력의 경우 예외를 던진다.
        """
        if self.kind == "real":
            return "https://openapi.koreainvestment.com:9443"
        elif self.kind == "virtual":
            return "https://openapivts.koreainvestment.com:29443"

        elif self.kind is None and input_url is not None:
            return input_url
        else:
            raise RuntimeError("invalid domain info")

    def is_real(self) -> bool:
        """
        실제 투자용 도메인 정보인지 여부를 반환한다. 
        """
        return self.kind == "real"


class AccessToken:
    def __init__(self, resp: NamedTuple) -> None:
        self.value: str = f"Bearer {str(resp.access_token)}"
        self.valid_until: datetime = self._get_valid_until(resp)

    def is_valid(self) -> bool:
        """
        access token이 유효한지 검사한다.
        """
        return datetime.now() < self.valid_until

    def _get_valid_until(self, resp: NamedTuple) -> datetime:
        """
        현재 시각 기준으로 access token의 유효기한을 반환한다.
        """
        time_margin = 60
        duration = int(resp.expires_in) - time_margin
        return datetime.now() + timedelta(seconds=duration)


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

        self.set_account(account_info)

    def set_account(self, account_info: Optional[Json]) -> None:
        """
        사용할 계좌 정보를 설정한다.
        account_info: 사용할 계좌 정보. { "account_code" : "[계좌번호 앞 8자리 숫자]", "product_code" : "[계좌번호 뒤 2자리 숫자]" }
        """
        if account_info is not None:
            self.account = to_namedtuple("account", account_info)

    # 인증-----------------

    def auth(self) -> None:
        """
        access token을 발급한다.
        """
        url_path = "/oauth2/tokenP"

        params = merge_json([
            self.get_api_key_data(),
            {
                "grant_type": "client_credentials"
            }
        ])

        r = self._send_post_request(
            url_path, tr_id=None, params=params, auth=False, hash=False)
        body = to_namedtuple("body", r.body)

        self.token = AccessToken(body)

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

    def get_hash_key(self, params: Json) -> str:
        """
        hash key 값을 가져온다. 
        """
        url_path = "/uapi/hashkey"
        r = self._send_post_request(
            url_path, tr_id=None, params=params, auth=False, hash=False)

        return r.body["HASH"]

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
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker
        }

        res = self._send_get_request(url_path, tr_id, params)
        return res.outputs[0]

    # 시세 조회------------

    # 잔고 조회------------
    def get_kr_buyable_cash(self) -> int:
        """
        구매 가능 현금(원화) 조회
        return: 해당 계좌의 구매 가능한 현금(원화)
        """
        url_path = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
        tr_id = "TTTC8908R"

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

        res = self._send_get_request(url_path, tr_id, params)
        output = res.outputs[0]
        return int(output["ord_psbl_cash"])

    def _get_kr_total_balance(self, extra_header: Json = dict(), extra_param: Json = dict()) -> APIResponse:
        """
        국내 주식 잔고의 조회 전체 결과를 반환한다.
        """
        url_path = "/uapi/domestic-stock/v1/trading/inquire-balance"
        tr_id = "TTTC8434R"

        extra_header = merge_json([{"tr_cont": ""}, extra_header])

        params = {
            "CANO": self.account.account_code,
            "ACNT_PRDT_CD": self.account.product_code,
            "AFHR_FLPR_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "FUND_STTL_ICLD_YN": "N",
            "INQR_DVSN": "01",
            "OFL_YN": "N",
            "PRCS_DVSN": "01",
            "UNPR_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }

        params = merge_json([params, extra_param])

        return self._send_get_request(url_path, tr_id, params, extra_header=extra_header)

    def get_kr_stock_balance(self) -> pd.DataFrame:
        """
        국내 주식 잔고 조회
        return: 국내 주식 잔고 정보를 DataFrame으로 반환
        """

        def to_dataframe(output: Json) -> pd.DataFrame:
            tdf = pd.DataFrame(output)
            if tdf.empty:
                return tdf

            tdf.set_index("pdno", inplace=True)
            cf1 = ["prdt_name", "hldg_qty", "ord_psbl_qty", "pchs_avg_pric",
                   "evlu_pfls_rt", "prpr", "bfdy_cprs_icdc", "fltt_rt"]
            cf2 = ["종목명", "보유수량", "매도가능수량", "매입단가", "수익율", "현재가", "전일대비", "등락"]
            tdf = tdf[cf1]
            tdf[cf1[1:]] = tdf[cf1[1:]].apply(pd.to_numeric)
            ren_dict = dict(zip(cf1, cf2))
            return tdf.rename(columns=ren_dict)

        max_count = 100
        outputs = []

        # 초기값
        extra_header = dict()
        extra_param = dict()

        for i in range(max_count):
            if i > 0:
                extra_header = {"tr_cont": "N"}    # 공백 : 초기 조회, N : 다음 데이터 조회

            res = self._get_kr_total_balance(
                extra_header=extra_header,
                extra_param=extra_param
            )
            df = to_dataframe(res.outputs[0])
            outputs.append(df)

            response_tr_cont = res.header["tr_cont"]
            no_more_data = response_tr_cont not in ["F", "M"]

            if no_more_data:
                break

            extra_param["CTX_AREA_FK100"] = res.body["ctx_area_fk100"]
            extra_param["CTX_AREA_NK100"] = res.body["ctx_area_nk100"]

        return pd.concat(outputs)

    def get_kr_deposit(self) -> int:
        """
        국내 주식 잔고의 총 예수금을 반환한다.
        """
        res = self._get_kr_total_balance()

        output2 = res.outputs[1]
        return int(output2[0]["dnca_tot_amt"])

    # 잔고 조회------------

    # 매매-----------------

    def _send_kr_stock_order(self, ticker: str, order_amount: int, price: int, buy: bool) -> Json:
        """
        국내 주식 매매(현금)
        """
        order_type = "00"  # 00: 지정가, 01: 시장가, ... (추후 옵션화 예정)
        url_path = "/uapi/domestic-stock/v1/trading/order-cash"

        if buy:
            tr_id = "TTTC0802U"  # buy
        else:
            tr_id = "TTTC0801U"  # sell

        params = {
            "CANO": self.account.account_code,
            "ACNT_PRDT_CD": self.account.product_code,
            "PDNO": ticker,
            "ORD_DVSN": order_type,
            "ORD_QTY": str(order_amount),
            "ORD_UNPR": str(price),
            "CTAC_TLNO": "",
            # "SLL_TYPE": "01",
            "ALGO_NO": ""
        }

        r = self._send_post_request(
            url_path, tr_id=tr_id, params=params, auth=True, hash=True)
        return r.outputs[0]

    def buy_kr_stock(self, ticker: str, order_amount: int, price: int) -> Json:
        """
        국내 주식 매수(현금)
        ticker: 종목코드
        order_amount: 주문 수량
        price: 주문 가격
        """
        return self._send_kr_stock_order(ticker, order_amount, price, True)

    def sell_kr_stock(self, ticker: str, order_amount: int, price: int) -> Json:
        """
        국내 주식 매매(현금)
        ticker: 종목코드
        order_amount: 주문 수량
        price: 주문 가격
        """
        return self._send_kr_stock_order(ticker, order_amount, price, False)

    # 매매-----------------

    # HTTTP----------------

    def _adjust_tr_id(self, tr_id: str) -> str:
        """
        모의 투자인 경우, tr_id를 필요에 따라 변경한다.
        """
        if not self.domain.is_real():
            if len(tr_id) >= 1 and tr_id[0] in ["T", "J", "C"]:
                return "V" + tr_id[1:]
        return tr_id

    def _send_get_request(self, url_path: str, tr_id: str, params: Json, extra_header: Json = dict()) -> APIResponse:
        """
        HTTP GET method로 request를 보내고 response를 반환한다. 
        """
        url, headers = self._http_request_parameters(
            url_path, tr_id, auth=True, extra_header=extra_header)
        return send_get_request(url, headers, params)

    def _send_post_request(self, url_path: str, tr_id: Optional[str], params: Json, auth: bool, hash: bool, extra_header: Json = dict()) -> APIResponse:
        """
        HTTP GET method로 request를 보내고 response를 반환한다. 
        """
        url, headers = self._http_request_parameters(
            url_path, tr_id, auth=auth, extra_header=extra_header)
        if hash:
            self.set_hash_key(headers, params)
        return send_post_request(url, headers, params)

    def _http_request_parameters(self, url_path: str, tr_id: Optional[str], auth: bool, extra_header: Json = dict()) -> Tuple[str, Json]:
        """
        http request용 파라미터를 튜플로 반환한다. 
        """
        url = self.domain.get_url(url_path)

        tr_id = self._adjust_tr_id(tr_id)

        headers = [
            get_base_headers(),
            self.get_api_key_data(),
        ]

        if tr_id is not None:
            headers.append({"tr_id": tr_id})

        if auth:
            if self.need_auth():
                self.auth()
            headers.append({
                "authorization": self.token.value,
            })

        headers.append(extra_header)

        headers = merge_json(headers)

        return url, headers

    # HTTTP----------------
