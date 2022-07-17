"""
request 관련 유틸리티 모듈
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

from typing import NamedTuple, Optional, Dict, Any, List
import json
import requests

Json = Dict[str, Any]


class APIRequestParameter(NamedTuple):
    """
    API request용 파라미터를 나타내는 클래스
    """
    url_path: str
    tr_id: Optional[str]
    params: Json
    requires_authentication: bool = True
    requires_hash: bool = False
    extra_header: Optional[Json] = None


class APIResponse:
    """
    API에서 반환된 응답을 나타내는 클래스
    """

    def __init__(self, resp: requests.Response) -> None:
        self.http_code: int = resp.status_code
        self.header: Json = self._header(resp)
        self.body: Json = resp.json()
        self.message: str = self._message()
        self.return_code: Optional[str] = self._return_code()
        self.outputs: List[Json] = self._outputs()

    def is_ok(self) -> bool:
        """
        아무런 오류가 없는 경우 True, 오류가 있는 경우 False를 반환한다.
        """
        return self.http_code == 200 and (self.return_code == "0" or self.return_code is None)

    def raise_if_error(self, check_http_error=True, check_return_code=True) -> None:
        """
        오류가 난 경우 예외를 던진다.
        """
        error_message = f"http response: {self.http_code}, " + \
                        f"return code: {self.return_code}. msg: {self.message}"

        if check_http_error and self.http_code != 200:
            raise RuntimeError(error_message)

        if check_return_code and self.return_code != "0" and self.return_code is not None:
            raise RuntimeError(error_message)

    def _message(self) -> str:
        """
        API의 response에서 응답 메시지를 찾아서 반환한다. 없는 경우 빈 문자열을 반환.
        """
        if "msg" in self.body:
            return self.body["msg"]

        if "msg1" in self.body:
            return self.body["msg1"]

        return ""

    def _return_code(self) -> Optional[str]:
        """
        API에서 성공/실패를 나타내는 return code를 찾아서 반환한다. 없는 경우 None을 반환
        """
        return self.body.get("rt_cd", None)

    def _outputs(self) -> List[Json]:
        """
        API의 output 값(ex> output, output1, output2)들을 list로 가져온다.
        뒤에 붙은 번호 순서대로(output이 있는 경우 제일 앞) 배치한다.
        """
        target_keys = ["output", "output1", "output2"]
        ret = [self.body[target]
               for target in target_keys if target in self.body]

        return ret

    def _header(self, resp: requests.Response) -> Json:
        """
        API의 response에서 header 정보를 찾아서 반환한다.
        """
        header = {}
        for key in resp.headers.keys():
            if key.islower():
                header[key] = resp.headers.get(key)
        return header


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


def send_get_request(url: str, headers: Json, params: Json, raise_flag: bool = True) -> APIResponse:
    """
    HTTP GET method로 request를 보내고 APIResponse 객체를 반환한다.
    """
    resp = requests.get(url, headers=headers, params=params)
    api_resp = APIResponse(resp)

    if raise_flag:
        api_resp.raise_if_error()

    return api_resp


def send_post_request(url: str, headers: Json, params: Json,
                      raise_flag: bool = True) -> APIResponse:
    """
    HTTP POST method로 request를 보내고 APIResponse 객체를 반환한다.
    """
    resp = requests.post(url, headers=headers, data=json.dumps(params))
    api_resp = APIResponse(resp)

    if raise_flag:
        api_resp.raise_if_error()

    return api_resp
