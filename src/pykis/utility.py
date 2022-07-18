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

from typing import Callable, Iterable, Optional, NamedTuple
from collections import namedtuple
import pandas as pd
from .request_utility import Json, APIResponse


def get_order_tr_id_from_market_code(market_code: str, is_buy: bool) -> str:
    """
    거래소 코드를 입력 받아서 해외 매매 주문 tr_id를 반환한다
    """
    market_code = market_code.upper()
    if market_code in ["NASD", "NAS", "NYSE", "AMEX", "AMS"]:
        return "JTTT1002U" if is_buy else "JTTT1006U"
    if market_code in ["SEHK", "HKS"]:
        return "TTTS1002U" if is_buy else "TTTS1001U"
    if market_code in ["SZAA", "SZS"]:  # 심천
        return "TTTS0305U" if is_buy else "TTTS0304U"
    if market_code in ["SHAA", "SHS"]:  # 상해
        return "TTTS0202U" if is_buy else "TTTS1005U"
    if market_code in ["TKSE", "TSE"]:
        return "TTTS0308U" if is_buy else "TTTS0307U"
    if market_code in ["HASE", "VNSE", "HSX", "HNX"]:
        return "TTTS0311U" if is_buy else "TTTS0310U"
    raise RuntimeError(f"invalid market code: {market_code}")


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


def get_continuous_query_code(is_kr: bool) -> str:
    """
    연속 querry 에 필요한 지역 관련 코드를 반환한다
    """
    return "100" if is_kr else "200"


def send_continuous_query(request_function: Callable[[Json, Json], APIResponse],
                          to_dataframe:
                          Callable[[APIResponse], pd.DataFrame],
                          is_kr: bool = True) -> pd.DataFrame:
    """
    조회 결과가 100건 이상 존재하는 경우 연속하여 query 후 전체 결과를 DataFrame으로 통합하여 반환한다.
    """
    max_count = 100
    outputs = []
    # 초기값
    extra_header = {}
    extra_param = {}
    for i in range(max_count):
        if i > 0:
            extra_header = {"tr_cont": "N"}    # 공백 : 초기 조회, N : 다음 데이터 조회
        res = request_function(
            extra_header=extra_header,
            extra_param=extra_param
        )
        output = to_dataframe(res)
        outputs.append(output)
        response_tr_cont = res.header["tr_cont"]
        no_more_data = response_tr_cont not in ["F", "M"]
        if no_more_data:
            break
        query_code = get_continuous_query_code(is_kr)
        extra_param[f"CTX_AREA_FK{query_code}"] = res.body[f"ctx_area_fk{query_code}"]
        extra_param[f"CTX_AREA_NK{query_code}"] = res.body[f"ctx_area_nk{query_code}"]
    return pd.concat(outputs)


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


def none_to_empty_dict(data: Optional[Json]) -> Json:
    """
    입력 값이 None인 경우에 빈 dictionary를 반환한다.
    """
    return data if data is not None else {}
