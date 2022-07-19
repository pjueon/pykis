"""
거래소 코드 변환 로직
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


class MarketCodeMap:
    """
    거래소 코드 변환 맵
    """

    def __init__(self) -> None:
        # 해외주식 잔고 API 문서에 따르면 NAS, NASD 의미가 일관적이지 않아서 확인 필요함
        self.map_3_to_4 = {
            "NAS": "NASD",
            "AMS": "AMEX",
            "TSE": "TKSE",
            "SHS": "SHAA",
            "SZS": "SZAA",
            "HSX": "VNSE",
            "HNX": "HASE",
        }

        self.map_4_to_3 = {
            value: key for key, value in self.map_3_to_4.items()
        }

    def _convert(self, market_code: str, is_3_to4: bool) -> str:
        """
        거래소 코드 변환용 내부 함수
        """
        market_code = market_code.upper()

        if is_3_to4:
            if market_code in self.map_4_to_3:
                return market_code
            convert_map = self.map_3_to_4
        else:
            if market_code in self.map_3_to_4:
                return market_code
            convert_map = self.map_4_to_3

        if market_code in convert_map:
            return convert_map[market_code]

        raise RuntimeError(f"failed to convert market code: {market_code}")

    def to_3(self, market_code: str) -> str:
        """
        거래소 코드를 입력받아 3글자 기반 방식으로 변환한다
        """
        return self._convert(market_code, False)

    def to_4(self, market_code: str) -> str:
        """
        거래소 코드를 입력받아 4글자 기반 방식으로 변환한다
        """
        return self._convert(market_code, True)
