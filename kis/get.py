import pickle
import requests
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import List

from kis.auth import KIS_APP_KEY, KIS_APP_SECRET, auth
from calc.math import StockAnalyzer


@dataclass
class StockExchange:
    code: str
    name: str
    stocks: List[str]


stocks_dir = Path(__file__).resolve().parent / "stocks"

exchange_list = [
    KRX := StockExchange(
        code="KRX",
        name="Korea Stock Exchange",
        stocks=pickle.loads((stocks_dir / "KRX.pickle").read_bytes()),
    ),
    HKS := StockExchange(
        code="HKS",
        name="Hong Kong Stock Exchange",
        stocks=pickle.loads((stocks_dir / "HKS.pickle").read_bytes()),
    ),
    NYS := StockExchange(
        code="NYS",
        name="New York Stock Exchange",
        stocks=pickle.loads((stocks_dir / "NYS.pickle").read_bytes()),
    ),
    NAS := StockExchange(
        code="NAS",
        name="Nasdaq Stock Exchange",
        stocks=pickle.loads((stocks_dir / "NAS.pickle").read_bytes()),
    ),
    AMS := StockExchange(
        code="AMS",
        name="Amex stock exchange",
        stocks=pickle.loads((stocks_dir / "AMS.pickle").read_bytes()),
    ),
    TSE := StockExchange(
        code="TSE",
        name="Tokyo Stock Exchange",
        stocks=pickle.loads((stocks_dir / "TSE.pickle").read_bytes()),
    ),
    SHS := StockExchange(
        code="SHS",
        name="Shanghai Stock Exchange",
        stocks=pickle.loads((stocks_dir / "SHS.pickle").read_bytes()),
    ),
    SZS := StockExchange(
        code="SZS",
        name="Shenzhen Stock Exchange",
        stocks=pickle.loads((stocks_dir / "SZS.pickle").read_bytes()),
    ),
    HSX := StockExchange(
        code="HSX",
        name="Ho Chi Minh City Stock Exchange",
        stocks=pickle.loads((stocks_dir / "HSX.pickle").read_bytes()),
    ),
    HNX := StockExchange(
        code="HNX",
        name="Hanoi Stock Exchange",
        stocks=pickle.loads((stocks_dir / "HNX.pickle").read_bytes()),
    ),
]


def daynight_consider(exchange_code: str):
    """exchange_code가 NAS/AMS/NYS 중 하나인 경우 주간 야간을 고려한 거래소 코드를 반환합니다."""

    exc_codes = {"AMS": "BAA", "NAS": "BAQ", "NYS": "BAY"}  # 각 거래소의 주간 거래소
    if exchange_code not in exc_codes.keys():
        return exchange_code

    res = requests.get(
        url="https://openapi.koreainvestment.com:9443/uapi/overseas-stock/v1/trading/dayornight",
        headers={
            "authorization": f"Bearer {auth.token}",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
            "tr_id": "JTTT3010R",
        },
    )
    is_daytime = True if res.json()["output"]["PSBL_YN"] == "N" else False
    return exc_codes[exchange_code] if is_daytime else exchange_code


class Stock:
    class _IncompleteIteration(Exception):
        """클래스 내부적으로 사용되는 미완료 여부 감지용 예외 클래스"""

    def __init__(self, *, code: str, exchange: StockExchange):
        self.code = code
        self.exchange = exchange
        self._history_iter = (
            self._domestic_history_iter
            if exchange is KRX
            else self._overseas_history_iter
        )

    def _domestic_history_iter(self, ref_day: datetime):
        """
        - ref_day로부터 최대 100개의 과거 데이터를 이터레이션합니다.
        - 국내(KRX)거래소 조회 시 사용됩니다.
        """
        res = requests.get(
            url="https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            headers={
                "authorization": f"Bearer {auth.token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "FHKST03010100",
            },
            params={
                "FID_COND_MRKT_DIV_CODE": "J",  # J=주식
                "FID_INPUT_ISCD": self.code,
                "FID_INPUT_DATE_1": datetime(  # 시작일: ref_day - 1년
                    year=ref_day.year - 1, month=ref_day.month, day=ref_day.day
                ).strftime("%Y%m%d"),
                "FID_INPUT_DATE_2": ref_day.strftime("%Y%m%d"),
                "FID_PERIOD_DIV_CODE": "D",  # 일봉
                "FID_ORG_ADJ_PRC": "1",  # 원주가
            },
        ).json()
        for ele in res["output2"]:
            if not ele["stck_clpr"]:
                raise self._IncompleteIteration
            clos = float(ele["stck_clpr"])
            low = float(ele["stck_lwpr"])
            high = float(ele["stck_hgpr"])
            typical_price = (clos + low + high) / 3
            yield {
                "date": datetime.strptime(ele["stck_bsop_date"], "%Y%m%d"),
                "price": typical_price,
                "low": low,
                "high": high,
                "tvol": float(ele["acml_vol"]),
                "tamt": float(ele["acml_tr_pbmn"]),
            }

    def _overseas_history_iter(self, ref_day: datetime):
        """
        - ref_day로부터 최대 100개의 과거 데이터를 이터레이션합니다.
        - 해외 거래소 조회 시 사용됩니다.
        """
        res = requests.get(
            url="https://openapi.koreainvestment.com:9443/uapi/overseas-price/v1/quotations/dailyprice",
            headers={
                "authorization": f"Bearer {auth.token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "HHDFS76240000",
            },
            params={
                "AUTH": "",
                "EXCD": daynight_consider(self.exchange.code),
                "SYMB": self.code,
                "GUBN": 0,  # 0:일, 1:주, 2:월
                "BYMD": ref_day.strftime("%Y%m%d"),
                "MODP": 0,
            },
        ).json()
        for ele in res["output2"]:
            if not ele["clos"]:
                raise self._IncompleteIteration
            clos = float(ele["clos"])
            low = float(ele["low"])
            high = float(ele["high"])
            typical_price = (clos + low + high) / 3
            yield {
                "date": datetime.strptime(ele["xymd"], "%Y%m%d"),
                "price": typical_price,
                "low": low,
                "high": high,
                "tvol": float(ele["tvol"]),
                "tamt": float(ele["tamt"]),
            }

    def analyzer(self, max_size: int = 100, ref_day: datetime = datetime.now()):
        """ref_day로부터 최대 max_size만큼의 과거 데이터가 담긴 StockAnalyzer를 생성하여 반환합니다."""

        bucket = defaultdict(list)  # 이터레이션 값이 누적되는 객체
        it = self._history_iter(ref_day)

        while len(bucket["date"]) < max_size:
            try:
                current = next(it)
                for key, value in current.items():
                    bucket[key].append(value)
            except StopIteration:
                for data in bucket.values():
                    del data[-1]  # 이전 호출 마지막과 다음 호출 처음이 겹치므로 제거
                # 마지막 날짜를 처음으로 해서 다시 호출
                it = self._history_iter(current["date"])
            except self._IncompleteIteration:  # max_size를 다 채울 수 없음
                break

        for key in bucket:  # 데이터를 과거 -> 현재 순서대로 정렬합니다.
            bucket[key].reverse()

        return StockAnalyzer(code=self.code, exchange=self.exchange, **bucket)

    def current(self):
        """현재 채결가"""
        if self.exchange is KRX:
            res = requests.get(
                url="https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-price",
                headers={
                    "authorization": f"Bearer {auth.token}",
                    "appkey": KIS_APP_KEY,
                    "appsecret": KIS_APP_SECRET,
                    "tr_id": "FHKST01010100",
                },
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": self.code,
                },
            ).json()
            price = res["output"]["stck_prpr"]
        else:
            res = requests.get(
                url="https://openapi.koreainvestment.com:9443/uapi/overseas-price/v1/quotations/price",
                headers={
                    "authorization": f"Bearer {auth.token}",
                    "appkey": KIS_APP_KEY,
                    "appsecret": KIS_APP_SECRET,
                    "tr_id": "HHDFS00000300",
                },
                params={
                    "AUTH": "",
                    "EXCD": daynight_consider(self.exchange.code),
                    "SYMB": self.code,
                },
            ).json()
            price = res["output"]["last"]
        return float(price) if price else None

    def __repr__(self) -> str:
        return f"<kis.get.Stock {self.code}/{self.exchange.code}>"


def cond_search_api_call(params: dict) -> List[StockAnalyzer]:
    """해외주식 조건검색 API call 함수"""  #! 국내주식도 적용해서 업데이트
    analyzers = []

    for exc_code in exchange_list:
        res = requests.get(
            url="https://openapi.koreainvestment.com:9443/uapi/overseas-price/v1/quotations/inquire-search",
            headers={
                "authorization": f"Bearer {auth.token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "HHDFS76410000",
                "custtype": "P",
            },
            params={"AUTH": "", "EXCD": exc_code} | params,
        ).json()
        for data in res["output2"]:
            analyzers.append(Stock(exchange=data["excd"], code=data["symb"]).analyzer())

    return analyzers


def current_price(x1, x2):
    """가격 범위로 검색합니다."""
    params = {"CO_YN_PRICECUR": "1", "CO_ST_PRICECUR": x1, "CO_EN_PRICECUR": x2}
    return cond_search_api_call(params)


def fluctuation_rate(x1, x2):
    """등락율 범위로 검색합니다."""
    params = {"CO_YN_RATE": "1", "CO_ST_RATE": x1, "CO_EN_RATE": x2}
    return cond_search_api_call(params)


def trading_volume(x1, x2):
    """거래량 범위로 검색합니다."""
    params = {"CO_YN_VOLUME": "1", "CO_ST_VOLUME": x1, "CO_EN_VOLUME": x2}
    return cond_search_api_call(params)


def trading_price(x1, x2):
    """거래대금 범위로 검색합니다."""
    params = {"CO_YN_AMT": "1", "CO_ST_AMT": x1, "CO_EN_AMT": x2}
    return cond_search_api_call(params)


def per(x1, x2):
    """PER(주가수익비율) 범위로 검색합니다."""
    params = {"CO_YN_PER": "1", "CO_ST_PER": x1, "CO_EN_PER": x2}
    return cond_search_api_call(params)


def eps(x1, x2):
    """EPS(주당순이익) 범위로 검색합니다."""
    params = {"CO_YN_EPS": "1", "CO_ST_EPS": x1, "CO_EN_EPS": x2}
    return cond_search_api_call(params)


def shares_amount(x1, x2):
    """발행 주식 수 범위로 검색합니다."""
    params = {"CO_YN_SHAR": "1", "CO_ST_SHAR": x1, "CO_EN_SHAR": x2}
    return cond_search_api_call(params)


def market_capitalization(x1, x2):
    """기업 시가총액 범위로 검색합니다."""
    params = {"CO_YN_VALX": "1", "CO_ST_VALX": x1, "CO_EN_VALX": x2}
    return cond_search_api_call(params)


def all(target_exchanges: List[StockExchange] = exchange_list) -> List[StockAnalyzer]:
    """
    - 증권 거래소의 모든 주식을 StockAnalyzer로 불러옵니다.
    - target_exchanges: 거래소 리스트 / default=모든 거래소
    """
    analyzers = []
    for exchange in target_exchanges:
        for cnt, code in enumerate(exchange.stocks):
            print("")
            analyzers.append(Stock(exchange=exchange, code=code).analyzer())
            print(
                f"[get.all] loading {exchange}: {cnt/len(exchange.stocks) * 100:.3f}%",
                end="\r",
            )
        print(f"[get.all] {exchange} loading complete")
    return analyzers
