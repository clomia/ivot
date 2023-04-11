""" API 인증을 추상화합니다. """

import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

APP_KEY = os.environ.get("APP_KEY")
APP_SECRET = os.environ.get("APP_SECRET")
CANO = os.environ.get("CANO")
ACNT_PRDT_CD = os.environ.get("ACNT_PRDT_CD")

class _OAuth:

    def __init__(self):
        self.approval_key = requests.post(
            url="https://openapi.koreainvestment.com:9443/oauth2/Approval",
            json={
                "grant_type": "client_credentials",
                "appkey": APP_KEY,
                "secretkey": APP_SECRET,
            },
        ).json()["approval_key"]
        self.refresh()

    def refresh(self):
        """ 토큰 갱신 """
        token_info = requests.post(
            url="https://openapi.koreainvestment.com:9443/oauth2/tokenP",
            json={
                "grant_type": "client_credentials",
                "appkey": APP_KEY,
                "appsecret": APP_SECRET
            },
        ).json()
        self._token = token_info["access_token"]
        self.expired = datetime.strptime(token_info["access_token_token_expired"], "%Y-%m-%d %H:%M:%S")

    @property
    def token(self):
        """ 유효한 토큰을 반환 """
        if self.expired < datetime.now():
            self.refresh()
        return self._token

    def hash(self, post:dict):
        """ POST Request Body값 암호화에 필요한 hash key 생성 """
        return requests.post(
            url="https://openapi.koreainvestment.com:9443/uapi/hashkey",
            headers={
                "content-Type": "application/json",
                "appKey": APP_KEY,
                "appSecret": APP_SECRET,
            },
            json=post
        ).json()["HASH"]

auth = _OAuth()