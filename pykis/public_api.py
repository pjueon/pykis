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



class DomainInfo:
    def __init__(self, kind = None, url = None) -> None:
        if kind == "real":
            self.url = "https://openapi.koreainvestment.com:9443"
        elif kind == "virtual":
            self.url = "https://openapivts.koreainvestment.com:29443"

        elif kind is None and url is not None:
            self.url = url
        else:
            raise Exception("invalid domain info")


class Api:
    def __init__(self, key_info, domain_info = DomainInfo(kind="real"), account_info = None) -> None:
        """
        key_info: API 사용을 위한 인증키 정보. appkey, appsecret
        domain_info: domain 정보 (실전/모의/etc)
        account_info: 사용할 계좌 정보. account_code, account_product_code 
        """
        return

    def set_account(self, account_info):
        """
        사용할 계좌 정보 설정.
        account_info: 
        """
        return
    

    # 인증-----------------
    def auth(self):
        """
        토큰 발급.
        """
        return


    def set_hash_key(self, header, param):
        """
        header에 hash key 설정.
        """
        return


    def get_hash_key(self, param):
        """
        hash key 값 가져오기.
        """
        return
    # 인증-----------------


    # 시세 조회------------
    def get_kr_stock_price(self, ticker: str):
        """
        국내 주식 현재가 조회
        ticker: 종목코드
        return: 해당 종목 현재가 (단위: 원)
        """
        return
    # 시세 조회------------

    # 잔고 조회------------
    def get_kr_buyable_cash(self):
        """
        구매 가능 현금(원화) 조회
        return: 해당 계좌의 구매 가능한 현금(원화)
        """
        return

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

