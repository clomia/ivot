""" API 인증을 추상화합니다. """

import os
from datetime import datetime

import requests

from system.logger import log

KIS_APP_KEY = os.environ.get("KIS_APP_KEY")
KIS_APP_SECRET = os.environ.get("KIS_APP_SECRET")
KIS_CANO = os.environ.get("KIS_CANO")
KIS_ACNT_PRDT_CD = os.environ.get("KIS_ACNT_PRDT_CD")


class _OAuth:
    def __init__(self):
        self.approval_key = requests.post(
            url="https://openapi.koreainvestment.com:9443/oauth2/Approval",
            json={
                "grant_type": "client_credentials",
                "appkey": KIS_APP_KEY,
                "secretkey": KIS_APP_SECRET,
            },
        ).json()["approval_key"]
        self.refresh()

    def refresh(self):
        """토큰 갱신"""
        token_info = requests.post(
            url="https://openapi.koreainvestment.com:9443/oauth2/tokenP",
            json={
                "grant_type": "client_credentials",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
            },
        ).json()
        self._token = token_info["access_token"]
        self.expired = datetime.strptime(
            token_info["access_token_token_expired"], "%Y-%m-%d %H:%M:%S"
        )

    @property
    def token(self):
        """유효한 토큰을 반환"""
        if self.expired < datetime.now():
            self.refresh()
            log.info("토큰이 만료되어 새로운 토큰이 발급되었습니다.")
        return self._token

    def hash(self, post: dict):
        """POST Request Body값 암호화에 필요한 hash key 생성"""
        return requests.post(
            url="https://openapi.koreainvestment.com:9443/uapi/hashkey",
            headers={
                "content-Type": "application/json",
                "appKey": KIS_APP_KEY,
                "appSecret": KIS_APP_SECRET,
            },
            json=post,
        ).json()["HASH"]


auth = _OAuth()
