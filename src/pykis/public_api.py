"""
pykist 패키지의 public api 모음
"""

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

from typing import NamedTuple, Optional, Tuple
import time
import pandas as pd

from .request_utility import *  # pylint: disable = wildcard-import, unused-wildcard-import
from .domain_info import DomainInfo
from .access_token import AccessToken
from .utility import *  # pylint: disable = wildcard-import, unused-wildcard-import
from .market_code_map import MarketCodeMap


class Api:  # pylint: disable=too-many-public-methods
    """
    pykis의 public api를 나타내는 클래스
    """

    def __init__(self, key_info: Json, domain_info: DomainInfo = DomainInfo(kind="real"),
                 account_info: Optional[Json] = None) -> None:
        """
        key_info: API 사용을 위한 인증키 정보. appkey, appsecret
        domain_info: domain 정보 (실전/모의/etc)
        account_info: 사용할 계좌 정보.
                    { "account_code" : "[계좌번호 앞 8자리 숫자]", "product_code" : "[계좌번호 뒤 2자리 숫자]" }
        """
        self.key: Json = key_info
        self.domain: DomainInfo = domain_info
        self.token: AccessToken = AccessToken()
        self.account: Optional[NamedTuple] = None

        self.set_account(account_info)
        self.market_code_map = MarketCodeMap()

    def set_account(self, account_info: Optional[Json]) -> None:
        """
        사용할 계좌 정보를 설정한다.
        account_info: 사용할 계좌 정보.
                    { "account_code" : "[계좌번호 앞 8자리 숫자]", "product_code" : "[계좌번호 뒤 2자리 숫자]" }
        """
        if account_info is not None:
            self.account = to_namedtuple("account", account_info)

    # 인증-----------------

    def create_token(self) -> None:
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

        req = APIRequestParameter(url_path, tr_id=None,
                                  params=params, requires_authentication=False, requires_hash=False)
        response = self._send_post_request(req)
        body = to_namedtuple("body", response.body)

        self.token.create(body)

    def need_authentication(self) -> bool:
        """
        authentication이 필요한지 여부를 반환한다.
        """
        return not self.token.is_valid()

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
        req = APIRequestParameter(url_path, tr_id=None,
                                  params=params, requires_authentication=False, requires_hash=False)
        response = self._send_post_request(req)

        return response.body["HASH"]

    def get_api_key_data(self) -> Json:
        """
        사용자의 api key 데이터를 반환한다.
        """
        return self.key

    # 인증-----------------

    # 시세 조회------------
    def get_kr_current_price(self, ticker: str) -> int:
        """
        국내 주식 현재가를 반환한다.
        ticker: 종목코드
        return: 해당 종목 현재가 (단위: 원)
        """
        info = self._get_kr_stock_current_price_info(ticker)
        price = info["stck_prpr"]

        return int(price)

    def get_kr_max_price(self, ticker: str) -> int:
        """
        국내 주식의 상한가를 반환한다.
        ticker: 종목코드
        return: 해당 종목의 상한가 (단위: 원)
        """
        info = self._get_kr_stock_current_price_info(ticker)
        price = info["stck_mxpr"]

        return int(price)

    def get_kr_min_price(self, ticker: str) -> int:
        """
        국내 주식의 하한가를 반환한다.
        ticker: 종목코드
        return: 해당 종목의 하한가 (단위: 원)
        """
        info = self._get_kr_stock_current_price_info(ticker)
        price = info["stck_llam"]

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

        req = APIRequestParameter(url_path, tr_id, params)
        res = self._send_get_request(req)
        return res.outputs[0]

    def _get_kr_history(self, ticker: str, time_unit: str = "D") -> APIResponse:
        """
        해당 종목코드의 과거 가격 조회한다.
        ticker: 종목 코드
        time_unit: 기간 분류 코드 (d/day-일, w/week-주, m/month-월)
        """
        time_unit = time_unit.upper()

        if time_unit in ["DAYS", "DAY"]:
            time_unit = "D"
        elif time_unit in ["WEEKS", "WEEK"]:
            time_unit = "W"
        elif time_unit in ["MONTHS", "MONTH"]:
            time_unit = "M"

        url_path = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
        tr_id = "FHKST01010400"

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker,
            "FID_PERIOD_DIV_CODE": time_unit,
            "FID_ORG_ADJ_PRC": "0000000001"
        }

        req = APIRequestParameter(url_path, tr_id, params)

        return self._send_get_request(req, raise_flag=False)

    def get_kr_ohlcv(self, ticker: str, time_unit: str = "D") -> pd.DataFrame:
        """
        해당 종목코드의 과거 가격 정보를 DataFrame으로 반환한다.
        ticker: 종목 코드
        time_unit: 기간 분류 코드 (D/day-일, W/week-주, M/month-월)
        데이터는 최근 30 일/주/월 데이터로 제한됨
        """
        res = self._get_kr_history(ticker, time_unit)
        if not res.is_ok() or len(res.outputs) == 0 or len(res.outputs[0]) == 0:
            return pd.DataFrame()

        date_column = ["Date"]
        other_colums = ["Open", "High", "Low", "Close", "Volume"]

        keys = ["stck_bsop_date", "stck_oprc",
                "stck_hgpr", "stck_lwpr", "stck_clpr", "acml_vol"]
        values = date_column + other_colums

        data = pd.DataFrame(res.outputs[0])

        data = data[keys]
        rename_map = dict(zip(keys, values))

        data.rename(columns=rename_map, inplace=True)

        data[date_column] = data[date_column].apply(pd.to_datetime)
        data[other_colums] = data[other_colums].apply(pd.to_numeric)
        data.set_index("Date", inplace=True)

        return data

    def _get_os_stock_current_price_info(self, ticker: str, market_code: str) -> Json:
        """
        해외 주식 현재가 시세 정보를 반환한다.
        ticker: 종목코드
        market_code: 거래소 코드 (NYS-뉴욕, NAS-나스닥, AMX-아멕스, etc)
        return: 해당 종목 현재 시세 정보
        """
        url_path = "/uapi/overseas-price/v1/quotations/price"

        tr_id = "HHDFS00000300"
        ticker = ticker.upper()
        market_code = market_code.upper()

        params = {
            "AUTH": "",
            "EXCD": market_code,
            "SYMB": ticker
        }

        req = APIRequestParameter(url_path, tr_id, params)
        res = self._send_get_request(req)
        return res.outputs[0]

    def get_os_current_price(self, ticker: str, market_code: str) -> float:
        """
        해외 주식 현재가를 반환한다.
        ticker: 종목코드
        market_code: 거래소 코드 (NYS-뉴욕, NAS-나스닥, AMX-아멕스, etc)
        return: 해당 종목 현재가 (단위: 해당 화폐)
        """
        info = self._get_os_stock_current_price_info(ticker, market_code)
        price = info["last"]

        return float(price)

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
            msg = "계좌가 설정되지 않았습니다. set_account를 통해 계좌 정보를 설정해주세요."
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

        req = APIRequestParameter(url_path, tr_id, params)
        res = self._send_get_request(req)
        output = res.outputs[0]
        return int(output["ord_psbl_cash"])

    def get_kr_stock_balance(self) -> pd.DataFrame:
        """
        국내 주식 잔고 조회
        return: 국내 주식 잔고 정보를 DataFrame으로 반환
        """

        def to_dataframe(res: APIResponse) -> pd.DataFrame:
            tdf = pd.DataFrame(res.outputs[0])
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

        def request_function(*args, **kwargs):
            return self._get_kr_total_balance(*args, **kwargs)

        return send_continuous_query(request_function, to_dataframe)

    def get_kr_deposit(self) -> int:
        """
        국내 주식 잔고의 총 예수금을 반환한다.
        """
        res = self._get_kr_total_balance()

        output2 = res.outputs[1]
        return int(output2[0]["dnca_tot_amt"])

    def get_os_stock_balance(self) -> pd.DataFrame:
        """
        해외 주식 잔고를 DataFrame으로 반환한다
        return: 미국 주식 잔고 정보를 DataFrame으로 반환
        """
        market_codes = ["NASD", "SEHK", "SHAA", "SZAA", "TKSE", "HASE", "VNSE"]
        datas = [self._get_os_stock_balance(market_code)
                 for market_code in market_codes]

        return pd.concat(datas)

    def _get_os_stock_balance(self, market_code: str) -> pd.DataFrame:
        """
        해외 주식 잔고 조회
        return: 해외 주식 잔고 정보를 DataFrame으로 반환
        """

        def to_dataframe(res: APIResponse) -> pd.DataFrame:
            tdf = pd.DataFrame(res.outputs[0])
            if tdf.empty:
                return tdf

            tdf.set_index("ovrs_pdno", inplace=True)
            cf1 = ["ovrs_item_name", "ovrs_cblc_qty", "ord_psbl_qty", "frcr_pchs_amt1",
                   "evlu_pfls_rt", "now_pric2", "ovrs_excg_cd", "tr_crcy_cd"]
            cf2 = ["종목명", "보유수량", "매도가능수량", "매입단가",
                   "수익율", "현재가", "거래소코드", "거래화폐코드"]
            tdf = tdf[cf1]
            tdf[cf1[1:-2]] = tdf[cf1[1:-2]].apply(pd.to_numeric)
            ren_dict = dict(zip(cf1, cf2))
            return tdf.rename(columns=ren_dict)

        def request_function(*args, **kwargs):
            return self._get_os_total_balance(market_code, *args, **kwargs)

        return send_continuous_query(request_function, to_dataframe)

    def _get_total_balance(self, is_kr: bool,
                           extra_header: Json = None,
                           extra_param: Json = None) -> APIResponse:
        """
        주식 잔고의 조회 전체 결과를 반환한다.
        """
        if is_kr:
            url_path = "/uapi/domestic-stock/v1/trading/inquire-balance"
            tr_id = "TTTC8434R"
        else:
            url_path = "/uapi/overseas-stock/v1/trading/inquire-balance"
            tr_id = "JTTT3012R"

        extra_header = none_to_empty_dict(extra_header)
        extra_param = none_to_empty_dict(extra_param)

        extra_header = merge_json([{"tr_cont": ""}, extra_header])
        query_code = get_continuous_query_code(is_kr)

        params = {
            "CANO": self.account.account_code,
            "ACNT_PRDT_CD": self.account.product_code,
            f"CTX_AREA_FK{query_code}": "",
            f"CTX_AREA_NK{query_code}": ""
        }

        params = merge_json([params, extra_param])
        req = APIRequestParameter(url_path, tr_id, params,
                                  extra_header=extra_header)
        return self._send_get_request(req)

    def _get_os_total_balance(self, market_code: str, extra_header: Json = None,
                              extra_param: Json = None) -> APIResponse:
        """
        해외 주식 잔고의 조회 전체 결과를 반환한다.
        """
        currency_code = get_currency_code_from_market_code(market_code)

        extra_param = merge_json([{
            "OVRS_EXCG_CD": market_code,
            "TR_CRCY_CD": currency_code,
        }, none_to_empty_dict(extra_param)])

        is_kr = False

        return self._get_total_balance(is_kr, extra_header, extra_param)

    def _get_kr_total_balance(self, extra_header: Json = None,
                              extra_param: Json = None) -> APIResponse:
        """
        국내 주식 잔고의 조회 전체 결과를 반환한다.
        """
        extra_param = merge_json([{
            "AFHR_FLPR_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "FUND_STTL_ICLD_YN": "N",
            "INQR_DVSN": "01",
            "OFL_YN": "N",
            "PRCS_DVSN": "01",
            "UNPR_DVSN": "01",
        }, none_to_empty_dict(extra_param)])

        is_kr = True

        return self._get_total_balance(is_kr, extra_header, extra_param)

    # 잔고 조회------------

    # 주문 조회------------

    def _get_kr_orders_once(self, extra_header: Json = None,
                            extra_param: Json = None) -> APIResponse:
        """
        취소/정정 가능한 국내 주식 주문 목록을 반환한다.
        한번만 실행.
        """
        url_path = "/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl"
        tr_id = "TTTC8036R"

        extra_header = none_to_empty_dict(extra_header)
        extra_param = none_to_empty_dict(extra_param)

        extra_header = merge_json([{"tr_cont": ""}, extra_header])
        query_code = get_continuous_query_code(True)

        params = {
            "CANO": self.account.account_code,
            "ACNT_PRDT_CD": self.account.product_code,
            f"CTX_AREA_FK{query_code}": "",
            f"CTX_AREA_NK{query_code}": "",
            "INQR_DVSN_1": "0",
            "INQR_DVSN_2": "0"
        }

        params = merge_json([params, extra_param])
        req = APIRequestParameter(url_path, tr_id, params,
                                  extra_header=extra_header)
        res = self._send_get_request(req)

        return res

    def _get_os_orders_once(self, markert_code: str, extra_header: Json = None,
                            extra_param: Json = None) -> APIResponse:
        """
        취소/정정 가능한 해외 주식 주문 목록을 반환한다.
        한번만 실행.
        """
        url_path = "/uapi/overseas-stock/v1/trading/inquire-nccs"
        tr_id = "JTTT3018R"

        extra_header = none_to_empty_dict(extra_header)
        extra_param = none_to_empty_dict(extra_param)
        markert_code = self.market_code_map.to_4(markert_code)

        extra_header = merge_json([{"tr_cont": ""}, extra_header])
        query_code = get_continuous_query_code(False)

        params = {
            "CANO": self.account.account_code,
            "ACNT_PRDT_CD": self.account.product_code,
            f"CTX_AREA_FK{query_code}": "",
            f"CTX_AREA_NK{query_code}": "",
            "OVRS_EXCG_CD": markert_code,
            "SORT_SQN": "DS",
        }

        params = merge_json([params, extra_param])
        req = APIRequestParameter(url_path, tr_id, params,
                                  extra_header=extra_header)
        res = self._send_get_request(req)

        return res

    def get_kr_orders(self) -> pd.DataFrame:
        """
        취소/정정 가능한 국내 주식 주문 목록을 DataFrame으로 반환한다.
        """
        def sell_or_buy(value):  # 01: 매도, 02: 매수
            return "매도" if value == "01" else "매수"

        def to_dataframe(res: APIResponse) -> pd.DataFrame:
            data = pd.DataFrame(res.outputs[0])
            if data.empty:
                return data

            data.set_index("odno", inplace=True)
            keys = ["pdno", "ord_qty", "psbl_qty", "ord_unpr", "sll_buy_dvsn_cd",
                    "ord_tmd", "ord_gno_brno", "orgn_odno"]
            values = ["종목코드", "주문수량", "정정취소가능수량",
                      "주문가격", "매수매도구분", "시간", "주문점", "원번호"]
            data = data[keys]
            sell_or_buy_column = "sll_buy_dvsn_cd"

            data[sell_or_buy_column] = data[sell_or_buy_column].apply(
                sell_or_buy)

            rename_map = dict(zip(keys, values))
            data = data.rename(columns=rename_map)

            return data

        return send_continuous_query(self._get_kr_orders_once, to_dataframe)

    def get_os_orders(self) -> pd.DataFrame:
        """
        미체결 해외 주식 주문 목록을 DataFrame으로 반환한다.
        """
        def sell_or_buy(value):  # 01: 매도, 02: 매수
            return "매도" if value == "01" else "매수"

        def to_dataframe(res: APIResponse) -> pd.DataFrame:
            data = pd.DataFrame(res.outputs[0])
            if data.empty:
                return data

            sell_or_buy_column = "sll_buy_dvsn_cd"
            market_code_column = "ovrs_excg_cd"

            data.set_index("odno", inplace=True)

            rename_map = {
                "pdno": "종목코드",
                "ft_ord_qty": "주문수량",
                "ft_ccld_qty": "체결수량",
                "nccs_qty": "미체결수량",
                "ft_ord_unpr3": "주문가격",
                sell_or_buy_column: "매수매도구분",
                "ord_tmd": "시간",
                "ord_gno_brno": "주문점",
                "orgn_odno": "원번호",
                market_code_column: "해외거래소코드",
                "tr_crcy_cd": "거래통화코드",
                "prcs_stat_name": "처리상태명",
                "rjct_rson_name": "거부사유명",
                "rjct_rson": "거부사유",
            }

            data = data[rename_map.keys()]

            data[sell_or_buy_column] = data[sell_or_buy_column].apply(
                sell_or_buy)

            data[market_code_column] = data[market_code_column].apply(
                self.market_code_map.to_3
            )

            data = data.rename(columns=rename_map)

            return data

        def request_function_factory(code: str):
            def request_function(*args, **kwargs):
                return self._get_os_orders_once(code, *args, **kwargs)

            return request_function

        outputs = [
            send_continuous_query(request_function_factory(code), to_dataframe)
            for code in self.market_code_map.codes_4
        ]

        return pd.concat(outputs)

    # 주문 조회------------

    # 매매-----------------
    def _send_kr_order(self, ticker: str, amount: int, price: int, buy: bool) -> Json:
        """
        국내 주식 매매(현금)
        """
        order_type = "00"  # 00: 지정가, 01: 시장가, ...
        if price <= 0:
            price = 0
            order_type = "01"   # 시장가

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
            "ORD_QTY": str(amount),
            "ORD_UNPR": str(price),
            "CTAC_TLNO": "",
            # "SLL_TYPE": "01",
            # "ALGO_NO": ""
        }

        req = APIRequestParameter(url_path, tr_id=tr_id,
                                  params=params, requires_authentication=True, requires_hash=True)

        response = self._send_post_request(req)
        return response.outputs[0]

    def buy_kr_stock(self, ticker: str, amount: int, price: int) -> Json:
        """
        국내 주식 매수(현금)
        ticker: 종목코드
        amount: 주문 수량
        price: 주문 가격
        """
        return self._send_kr_order(ticker, amount, price, True)

    def sell_kr_stock(self, ticker: str, amount: int, price: int) -> Json:
        """
        국내 주식 매매(현금)
        ticker: 종목코드
        amount: 주문 수량
        price: 주문 가격
        """
        return self._send_kr_order(ticker, amount, price, False)

    def _send_os_order(self, ticker: str, market_code: str,  # pylint: disable=too-many-arguments
                       order_amount: int, price: float, buy: bool) -> Json:
        """
        해외 주식 매매
        """
        order_type = "00"  # 00: 지정가, 01: 시장가, ...
        price_as_str = f"{price:.2f}"
        market_code = self.market_code_map.to_4(market_code)

        if price <= 0:
            price_as_str = "0"
            order_type = "01"   # 시장가

        url_path = "/uapi/overseas-stock/v1/trading/order"

        tr_id = get_order_tr_id_from_market_code(market_code, buy)

        params = {
            "CANO": self.account.account_code,
            "ACNT_PRDT_CD": self.account.product_code,
            "PDNO": ticker,
            "OVRS_EXCG_CD": market_code,
            "ORD_DVSN": order_type,
            "ORD_QTY": str(order_amount),
            "OVRS_ORD_UNPR": price_as_str,
            "ORD_SVR_DVSN_CD": "0",
        }

        req = APIRequestParameter(url_path, tr_id=tr_id,
                                  params=params, requires_authentication=True, requires_hash=True)

        response = self._send_post_request(req)
        return response.outputs[0]

    def buy_os_stock(self, market_code: str, ticker: str,
                     amount: int, price: float):
        """
        해외 주식 매수 주문)
        ticker: 종목 코드
        market_code: 거래소 코드
        amount: 주문 수량
        price: 매매 가격 (1주당 가격, 해당 화폐)
        """
        return self._send_os_order(ticker, market_code, amount, price, True)

    def sell_os_stock(self, market_code: str, ticker: str,
                      amount: int, price: float):
        """
        해외 주식 매수 주문
        ticker: 종목 코드
        market_code: 거래소 코드
        amount: 주문 수량
        price: 매매 가격 (1주당 가격, 해당 화폐)
        """
        return self._send_os_order(ticker, market_code, amount, price, False)

    # 매매-----------------

    # 정정/취소-------------
    def _revise_cancel_kr_orders(self,  # pylint: disable=too-many-arguments
                                 order_number: str,
                                 is_cancel: bool,
                                 price: int,
                                 amount: Optional[int] = None,
                                 order_branch: str = "06010"
                                 ) -> Json:
        """
        국내 주식 주문을 정정 또는 취소한다
        order_number: 주문 번호
        order_branch: 주문점(통상 06010)
        amount: 정정/취소 적용할 주문의 수량
        price: 정정할 주문의 가격
        is_cancel: 정정구분(취소-True, 정정-False)
        return: 서버 response
        """
        url_path = "/uapi/domestic-stock/v1/trading/order-rvsecncl"
        tr_id = "TTTC0803U"

        order_dv: str = "00"  # order_dv: 주문유형(00-지정가)
        cancel_dv: str = "02" if is_cancel else "01"

        apply_all = "N"  # apply_all: 잔량전부주문여부(Y-잔량전부, N-잔량일부)

        if amount is None or amount <= 0:
            apply_all = "Y"
            amount = 1

        params = {
            "CANO": self.account.account_code,
            "ACNT_PRDT_CD": self.account.product_code,
            "KRX_FWDG_ORD_ORGNO": order_branch,
            "ORGN_ODNO": order_number,
            "ORD_DVSN": order_dv,
            "RVSE_CNCL_DVSN_CD": cancel_dv,
            "ORD_QTY": str(amount),
            "ORD_UNPR": str(price),
            "QTY_ALL_ORD_YN": apply_all
        }

        req = APIRequestParameter(url_path, tr_id=tr_id,
                                  params=params, requires_authentication=True, requires_hash=True)

        res = self._send_post_request(req)
        return res.body

    def cancel_kr_order(self, order_number: str, amount: Optional[int] = None,
                        order_branch: str = "06010") -> Json:
        """
        국내 주식 주문을 취소한다.
        order_number: 주문 번호.
        amount: 취소할 수량. 지정하지 않은 경우 잔량 전부 취소.
        return: 서버 response.
        """

        return self._revise_cancel_kr_orders(order_number=order_number,
                                             is_cancel=True,
                                             amount=amount,
                                             price=1,
                                             order_branch=order_branch)

    def cancel_all_kr_orders(self) -> None:
        """
        미체결된 모든 국내 주식 주문들을 취소한다.
        """
        data = self.get_kr_orders()
        orders = data.index.to_list()
        branchs = data["주문점"].to_list()
        delay = 0.2  # sec

        for order, branch in zip(orders, branchs):
            self.cancel_kr_order(order, order_branch=branch)
            time.sleep(delay)

    def revise_kr_order(self, order_number: str,
                        price: int,
                        amount: Optional[int] = None,
                        order_branch: str = "06010") -> Json:
        """
        국내 주식 주문의 가격을 정정한다.
        order_number: 주문 번호.
        price: 정정할 1주당 가격.
        amount: 정정할 수량. 지정하지 않은 경우 잔량 전부 정정.
        return: 서버 response.
        """

        return self._revise_cancel_kr_orders(order_number=order_number,
                                             is_cancel=False,
                                             amount=amount,
                                             price=price,
                                             order_branch=order_branch)
    # 정정/취소-------------

    # HTTTP----------------

    def _send_get_request(self, req: APIRequestParameter, raise_flag: bool = True) -> APIResponse:
        """
        HTTP GET method로 request를 보내고 response를 반환한다.
        """
        url = self.domain.get_url(req.url_path)
        headers = self._parse_headers(req)
        return send_get_request(url, headers, req.params, raise_flag=raise_flag)

    def _send_post_request(self, req: APIRequestParameter, raise_flag: bool = True) -> APIResponse:
        """
        HTTP GET method로 request를 보내고 response를 반환한다.
        """
        url = self.domain.get_url(req.url_path)
        headers = self._parse_headers(req)

        if req.requires_hash:
            self.set_hash_key(headers, req.params)
        return send_post_request(url, headers, req.params, raise_flag=raise_flag)

    def _parse_headers(self, req: APIRequestParameter) -> Tuple[str, Json]:
        """
        API에 request에 필요한 header를 구해서 튜플로 반환한다.
        """

        headers = [
            get_base_headers(),
            self.get_api_key_data(),
        ]

        tr_id = self.domain.adjust_tr_id(req.tr_id)

        if tr_id is not None:
            headers.append({"tr_id": tr_id})

        if req.requires_authentication:
            if self.need_authentication():
                self.create_token()

            headers.append({
                "authorization": self.token.value,
            })

        extra_header = none_to_empty_dict(req.extra_header)
        headers.append(extra_header)

        headers = merge_json(headers)

        return headers

    # HTTTP----------------
