"""
pykis의 AccessToken 클래스를 담기 위한 모듈
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

from datetime import datetime, timedelta
from typing import NamedTuple, Optional


class AccessToken:
    """
    인증용 토큰 정보를 담을 클래스
    """

    def __init__(self) -> None:
        self.value: Optional[str] = None
        self.valid_until: Optional[datetime] = None

    def create(self, resp: NamedTuple) -> None:
        """
        Token을 생성한다.
        """
        self.value: str = f"Bearer {str(resp.access_token)}"
        self.valid_until: datetime = self._valid_until(resp)

    def _valid_until(self, resp: NamedTuple) -> datetime:
        """
        현재 시각 기준으로 Token의 유효기한을 반환한다.
        """
        time_margin = 60
        duration = int(resp.expires_in) - time_margin
        return datetime.now() + timedelta(seconds=duration)

    def is_valid(self) -> bool:
        """
        Token이 유효한지 검사한다.
        """
        return self.value is not None and \
            self.valid_until is not None and \
            datetime.now() < self.valid_until
