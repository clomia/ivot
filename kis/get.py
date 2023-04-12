import pickle
import requests
from collections import defaultdict
from datetime import datetime
from typing import List

from kis.auth import APP_KEY, APP_SECRET, auth
from calc.math import StockAnalyzer

with (
    open(f"symbols/AMS.pickle", "rb") as ams_f,
    open(f"symbols/NAS.pickle", "rb") as nas_f,
    open(f"symbols/NYS.pickle", "rb") as nys_f,
):
    ams_symbols: list = pickle.load(ams_f)
    nas_symbols: list = pickle.load(nas_f)
    nys_symbols: list = pickle.load(nys_f)

# 거래소 코드는 API 요청시에만 주/야를 구분합니다. 정제된 데이터에 주간 거래소 코드를 사용하지 않습니다.
exchange_list = ["AMS", "NAS", "NYS"]


def daynight_consider(exchange_code: str):
    """주간인 경우 주간 거래소 코드로 변환합니다."""
    daytime = {"AMS": "BAA", "NAS": "BAQ", "NYS": "BAY"}  # 각 거래소의 주간 거래소
    res = requests.get(
        url="https://openapi.koreainvestment.com:9443/uapi/overseas-stock/v1/trading/dayornight",
        headers={
            "authorization": f"Bearer {auth.token}",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET,
            "tr_id": "JTTT3010R",
        },
    )
    is_daytime = True if res.json()["output"]["PSBL_YN"] == "N" else False
    return daytime[exchange_code] if is_daytime else exchange_code


class NoMoreData(Exception):
    """더이상 데이터가 없어서 작업을 완료할 수 없습니다."""


class StockPrice:
    def __init__(self, *, exchange: str, symbol: str):
        self.symbol = symbol
        self.exchange = exchange

    def _history_iter(self, ref_day: datetime):
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
                "EXCD": daynight_consider(self.exchange),
                "SYMB": self.symbol,
                "GUBN": 0,  # 0:일, 1:주, 2:월
                "BYMD": ref_day.strftime("%Y%m%d"),
                "MODP": 0,
            },
        ).json()
        for ele in res["output2"]:
            if not ele["clos"]:
                raise NoMoreData
            yield {
                "date": datetime.strptime(ele["xymd"], "%Y%m%d"),
                "price": float(ele["clos"]),
                "low": float(ele["low"]),
                "high": float(ele["high"]),
                "tvol": float(ele["tvol"]),
                "tamt": float(ele["tamt"]),
            }

    def analyzer(self, size: int = 100, ref_day: datetime = datetime.now()):
        """
        - ref_day로부터 size만큼의 과거 데이터가 담긴 StockAnalyzer를 생성하여 반환합니다.
        - 존재하는 과거데이터가 size 보다 작은 경우 NoMoreData를 raise합니다.
        """
        total = defaultdict(list)

        it = self._history_iter(ref_day)
        while len(total["date"]) < size:
            try:
                current = next(it)
                for key, value in current.items():
                    total[key].append(value)
            except StopIteration:  # 이전 호출 마지막과 다음 호출 처음이 겹치므로 제거
                for data in total.values():
                    del data[-1]
                it = self._history_iter(current["date"])
        return StockAnalyzer(symbol=self.symbol, exchange=self.exchange, **total)

    def current(self):
        """현재 채결가"""
        res = requests.get(
            url="https://openapi.koreainvestment.com:9443/uapi/overseas-price/v1/quotations/price",
            headers={
                "authorization": f"Bearer {auth.token}",
                "appkey": APP_KEY,
                "appsecret": APP_SECRET,
                "tr_id": "HHDFS00000300",
            },
            params={
                "AUTH": "",
                "EXCD": daynight_consider(self.exchange),
                "SYMB": self.symbol,
            },
        ).json()
        return float(res["output"]["last"])


class Explorer:
    def cond_search_api_call(self, params: dict) -> List[StockAnalyzer]:
        """해외주식 조건검색 API call 함수"""
        analyzers = []

        for exc_code in exchange_list:
            res = requests.get(
                url="https://openapi.koreainvestment.com:9443/uapi/overseas-price/v1/quotations/inquire-search",
                headers={
                    "authorization": f"Bearer {auth.token}",
                    "appkey": APP_KEY,
                    "appsecret": APP_SECRET,
                    "tr_id": "HHDFS76410000",
                    "custtype": "P",
                },
                params={"AUTH": "", "EXCD": exc_code} | params,
            ).json()
            for data in res["output2"]:
                try:
                    analyzers.append(
                        StockPrice(
                            exchange=data["excd"], symbol=data["symb"]
                        ).analyzer()
                    )
                except NoMoreData:
                    continue

        return analyzers

    def current_price(self, x1, x2) -> List[StockAnalyzer]:
        """가격 범위로 검색합니다."""
        params = {"CO_YN_PRICECUR": "1", "CO_ST_PRICECUR": x1, "CO_EN_PRICECUR": x2}
        return self.cond_search_api_call(params)

    def fluctuation_rate(self, x1, x2):
        """등락율 범위로 검색합니다."""
        params = {"CO_YN_RATE": "1", "CO_ST_RATE": x1, "CO_EN_RATE": x2}
        return self.cond_search_api_call(params)

    def trading_volume(self, x1, x2):
        """거래량 범위로 검색합니다."""
        params = {"CO_YN_VOLUME": "1", "CO_ST_VOLUME": x1, "CO_EN_VOLUME": x2}
        return self.cond_search_api_call(params)

    def trading_price(self, x1, x2):
        """거래대금 범위로 검색합니다."""
        params = {"CO_YN_AMT": "1", "CO_ST_AMT": x1, "CO_EN_AMT": x2}
        return self.cond_search_api_call(params)

    def per(self, x1, x2):
        """PER(주가수익비율) 범위로 검색합니다."""
        params = {"CO_YN_PER": "1", "CO_ST_PER": x1, "CO_EN_PER": x2}
        return self.cond_search_api_call(params)

    def eps(self, x1, x2):
        """EPS(주당순이익) 범위로 검색합니다."""
        params = {"CO_YN_EPS": "1", "CO_ST_EPS": x1, "CO_EN_EPS": x2}
        return self.cond_search_api_call(params)

    def shares_amount(self, x1, x2):
        """발행 주식 수 범위로 검색합니다."""
        params = {"CO_YN_SHAR": "1", "CO_ST_SHAR": x1, "CO_EN_SHAR": x2}
        return self.cond_search_api_call(params)

    def market_capitalization(self, x1, x2):
        """기업 시가총액 범위로 검색합니다."""
        params = {"CO_YN_VALX": "1", "CO_ST_VALX": x1, "CO_EN_VALX": x2}
        return self.cond_search_api_call(params)

    def filter(self):
        pass
