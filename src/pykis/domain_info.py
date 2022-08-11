"""
pykis의 DomainInfo 클래스를 담기 위한 모듈
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

from typing import Optional


class DomainInfo:
    """
    url 도메인 정보를 나타내는 클래스. (실제 투자, 모의 투자, etc)
    """

    def __init__(self, kind: Optional[str] = None, url: Optional[str] = None) -> None:
        self.kind = kind
        self.base_url = self._base_url(url)

    def get_url(self, url_path: str):
        """
        url_path를 입력받아서 전체 url을 반환한다.
        """
        separator = "" if url_path.startswith("/") else "/"
        return f"{self.base_url}{separator}{url_path}"

    def _base_url(self, input_url: Optional[str]) -> str:
        """
        domain 정보를 나타내는 base url 반환한다. 잘못된 입력의 경우 예외를 던진다.
        """
        if self.kind == "real":
            return "https://openapi.koreainvestment.com:9443"

        if self.kind == "virtual":
            return "https://openapivts.koreainvestment.com:29443"

        if self.kind is None and input_url is not None:
            return input_url

        raise RuntimeError("invalid domain info")

    def is_real(self) -> bool:
        """
        실제 투자용 도메인 정보인지 여부를 반환한다.
        """
        return self.kind == "real"

    def is_virtual(self) -> bool:
        """
        모의 투자용 도메인 정보인지 여부를 반환한다.
        """
        return self.kind == "virtual"

    def adjust_tr_id(self, tr_id: Optional[str]) -> Optional[str]:
        """
        모의 투자인 경우, tr_id를 필요에 따라 변경한다.
        """
        if tr_id is not None and self.is_virtual():
            if len(tr_id) >= 1 and tr_id[0] in ["T", "J", "C"]:
                return "V" + tr_id[1:]
        return tr_id
