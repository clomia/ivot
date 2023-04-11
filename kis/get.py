import pickle
import requests
from datetime import datetime

import numpy as np

from kis.auth import APP_KEY, APP_SECRET, auth

with (
    open(f"symbols/AMS.pickle", "rb") as ams_f,
    open(f"symbols/NAS.pickle", "rb") as nas_f,
    open(f"symbols/NYS.pickle", "rb") as nys_f,
):
    ams_symbols: list = pickle.load(ams_f)
    nas_symbols: list = pickle.load(nas_f)
    nys_symbols: list = pickle.load(nys_f)


class Explorer:
    def __init__(self, *, symbol: str, exchange: str):
        self.symbol = symbol
        self.exchange = exchange

    def price_history_iter(self, ref_day: datetime):
        """ref_day로부터 100일간의 시세를 이터레이션합니다."""
        res = requests.get(
            url="https://openapi.koreainvestment.com:9443/uapi/overseas-price/v1/quotations/dailyprice",
            headers={
                "authorization": f"Bearer {auth.token}",
                "appkey": APP_KEY,
                "appsecret": APP_SECRET,
                "tr_id": "HHDFS76240000",
            },
            params={
                "AUTH": "",
                "EXCD": self.exchange,
                "SYMB": self.symbol,
                "GUBN": 0,  # 0:일, 1:주, 2:월
                "BYMD": ref_day.strftime("%Y%m%d"),
                "MODP": 0,
            },
        )
        for ele in res.json()["output2"]:
            yield {
                "date": datetime.strptime(ele["xymd"], "%Y%m%d"),
                "clos": float(ele["clos"]),
                "high": float(ele["high"]),
                "low": float(ele["low"]),
                "tvol": float(ele["tvol"]),
                "tamt": float(ele["tamt"]),
            }

    def price_history(self, size: int = 100, ref_day: datetime = datetime.now()):
        """
        - 이렇게 6개의 array가 들어있는 dict를 반환합니다.
            - date: 날짜
            - clos: 종가
            - high: 고가
            - low: 저가
            - tvol: 거래량
            - tamt: 거래대금
        """
        data = {
            "date": [],
            "clos": [],
            "high": [],
            "low": [],
            "tvol": [],
            "tamt": [],
        }

        it = self.price_history_iter(ref_day)
        while len(data["date"]) < size:
            try:
                from_iter = next(it)
                data["date"].append(from_iter["date"])
                data["clos"].append(from_iter["clos"])
                data["high"].append(from_iter["high"])
                data["low"].append(from_iter["low"])
                data["tvol"].append(from_iter["tvol"])
                data["tamt"].append(from_iter["tamt"])
            except StopIteration:
                for lst in data.values():
                    del lst[-1]  # 이전 호출 마지막과 다음 호출 처음이 겹치므로 제거
                it = self.price_history_iter(from_iter["date"])
        return {k: np.array(v) for k, v in data.items()}
