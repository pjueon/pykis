# pykis
- pykis는 한국투자증권에서 제공하는 Open Trading API를 쉽게 사용하기 위한 **비공식** python wrapper입니다. 
- 기존 eFriend expert (HTS 프로그램) 연동 방식 API 대비 다음과 같은 장점들이 있습니다. 
  - Web API 방식 사용 
  - 별도의 HTS 프로그램에 의존하지 않음
  - 사용 가능 환경(OS)에 제한이 없음

- 기존 eFriend expert 연동 방식 API를 사용하는 python 패키지는 [pjueon/eFriendPy](https://github.com/pjueon/eFriendPy)를 참고하세요.


## 사용전 유의사항 
### license 관련
pykis는 Apache-2.0 license를 따릅니다. 
- Apache-2.0 license에서 규정하는 조건 안에서 자유롭게 수정/재배포/사용이 가능합니다. 자세한 사항은 LICENSE 파일을 참고 바랍니다.
- pykis의 동작에는 불완전한 부분이나 버그가 있을 수 있습니다. 또한 pykis의 API는 언제든 변경될 수 있습니다.
- pykis의 제작자([pjueon](https://github.com/pjueon))는 이 코드에 대해서 어떤 것도 보장하지 않습니다. 코드 사용중 생긴 **어떠한 종류의 피해(ex> 버그, 사용자의 실수, 투자로 인한 손실 등)에 대해서도 책임지지 않습니다.**

### KIS Developers 서비스 신청
- pykis를 사용하기 위해서는 한국투자증권 홈페이지에서 KIS Developers 서비스 신청을 통해 API key를 발급받아야 합니다.
- KIS Developers 서비스 신청방법은 한국투자증권의 [공식 wikidocs](https://wikidocs.net/159333)를 참고하세요.

### 기타

- pykis는 개인 투자 용도로만 개발되었습니다. 
- pykis는 아직 개발 단계입니다. 버그나 기능 요청 등의 feedback은 issue나 pull request를 통해 부탁드립니다. 

## 패키지 설치 
- pykis는 현재 개발 단계로 수정이 잦습니다. git을 통해 해당 repository를 clone하여 사용하세요.  
```shell
git clone https://github.com/pjueon/pykis.git
```
- 추후 pip 를 통해 설치할 수 있도록 정식 패키징 예정입니다. 


## API 기본 사용법 
### 패키지 import 
```python
import pykis
```

### `Api` 객체 생성
실제 계좌를 사용하는 경우
```python
# API 사용을 위한 API key정보 및 계좌 정보를 설정합니다. 
# 별도의 파일(json, yaml, xml, etc) 등에 내용을 저장하여 불러오는 것을 추천합니다. 
# key 정보는 절대 외부로 유출되지 않도록 주의하시고, 유출시 즉시 재발급 하시기 바랍니다.  
keys = {                
	"key_info":         # KIS Developers 서비스 신청을 통해 발급받은 API key 정보
	{
		"appkey": "[발급 받은 APP Key]",                  
		"appsecret": "[발급 받은 APP Secret]" 
	},
	"account_info" :    # 사용할 계좌 정보
	{
		"account_code": "[API를 신청한 종합 계좌번호(계좌번호 앞자리 8자리 숫자)]",   
		"product_code": "[계좌번호의 끝자리 2자리 숫자]"             # ex> "01", "22", etc
	}
}

# API 객체 생성 
api = pykis.Api(key_info=keys["key_info"], account_info=keys["account_info"])
```

모의 계좌를 사용하는 경우 
```python
domain = pykis.DomainInfo(kind="virtual")


# API 객체 생성 
api = pykis.Api(key_info=keys["key_info"], domain_info=domain, account_info=keys["account_info"])
```

### 사용 계좌 변경
```python
account_info = {    # 사용할 계좌 정보
	"account_code": "[API를 신청한 종합 계좌번호(계좌번호 앞자리 8자리 숫자)]",   
	"product_code": "[계좌번호의 끝자리 2자리 숫자]"             # ex> "01", "22", etc
}

api.set_account(account_info)
```

### 거래 가능 현금 조회
```python
cash = api.get_kr_buyable_cash()
print(f"거래 가능 현금: {cash} 원")
```

### 국내 주식 현재가 조회
```python
ticker = "005930"   # 삼성전자 종목코드
price = api.get_kr_stock_price(ticker)
print(f"삼성전자 현재가: {price} 원")
```

### 국내 주식 잔고 조회 
```python
# DataFrame 형태로 국내 주식 잔고 반환 
stock = api.get_kr_stock_balance()
print(f"보유중인 국내 주식: \n{stock}")
```

### 국내 주식 총 예수금 조회 
```python
deposit = api.get_kr_deposit()
print(f"총 예수금: {deposit} 원")
```

### 국내 주식 매수 주문
```python
ticker = "005930"   # 삼성전자 종목코드
price = 100000      # 매수 가격 예시

# 종목코드 ticker인 국내 주식 1주를 지정가로 매수 주문 
ret = api.buy_kr_stock(ticker, 1, price=price)

# 반환값: 서버 응답 (주문 번호 등의 정보)
print(ret)
```

### 국내 주식 매도 주문 
```python
ticker = "005930"   # 삼성전자 종목코드
price = 100000      # 매수 가격 예시

# 종목코드 ticker인 국내 주식 1주를 지정가로 매도 주문 
ret = api.sell_kr_stock(ticker, 1, price=price)

# 반환값: 서버 응답 (주문 번호 등의 정보)
print(ret)
```


## 관련 참고 자료
- [한국투자증권 KIS Developers](https://apiportal.koreainvestment.com)
- [한국투자증권 Open Trading API Github](https://github.com/koreainvestment/open-trading-api)
- [한국투자증권 Wikidocs](https://wikidocs.net/profile/info/book/13688)