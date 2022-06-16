

class Api:
    def __init__(self, key_info) -> None:
        """
        key_info: API 사용을 위한 인증키 정보
        """
        return

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
    def get_kr_buyable_cash(self, account_code: str):
        """
        구매 가능 현금(원화) 조회
        account_code: 조회하려는 계좌 정보
        return: 해당 계좌의 구매 가능한 현금(원화)
        """
        return

    def get_kr_stock_balance(self, account_code: str):
        """
        국내 주식 잔고 조회
        account_code: 조회하려는 계좌 정보
        return: 국내 주식 잔고 정보를 DataFrame으로 반환
        """
        return
    # 잔고 조회------------

    # 매매-----------------
    def buy_kr_stock(self, ticker: str, order_amount: int, price: int, account_code: str):
        """
        국내 주식 매수(현금)
        ticker: 종목코드
        order_amount: 주문 수량
        price: 주문 가격
        account_code: 매매를 진행하려는 계좌 정보
        """
        return

    def sell_kr_stock(self, ticker: str, order_amount: int, price: int, account_code: str):
        """
        국내 주식 매매(현금)
        ticker: 종목코드
        order_amount: 주문 수량
        price: 주문 가격
        account_code: 매매를 진행하려는 계좌 정보
        """
        return
    # 매매-----------------

