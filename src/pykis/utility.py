"""
pykis의 각종 유틸리티들을 모아둔 모듈
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


def get_currency_code_from_market_code(market_code: str) -> str:
    """
    거래소 코드를 입력 받아서 거래통화코드를 반환한다
    """
    market_code = market_code.upper()
    if market_code in ["NASD", "NAS", "NYSE", "AMEX", "AMS"]:
        return "USD"
    if market_code in ["SEHK", "HKS"]:
        return "HKD"
    if market_code in ["SHAA", "SZAA", "SHS", "SZS"]:
        return "CNY"
    if market_code in ["TKSE", "TSE"]:
        return "JPN"
    if market_code in ["HASE", "VNSE", "HSX", "HNX"]:
        return "VND"
    raise RuntimeError(f"invalid market code: {market_code}")


def get_continuous_querry_code(is_kr: bool) -> str:
    """
    연속 querry 에 필요한 지역 관련 코드를 반환한다
    """
    return "100" if is_kr else "200"
