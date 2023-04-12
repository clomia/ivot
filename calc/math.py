from math import sqrt
from typing import List
from datetime import datetime
from collections import defaultdict

import numpy as np


class StockAnalyzer:
    def __init__(
        self,
        *,
        symbol: str,  # 종목코드
        exchange: str,  # 거래소코드
        date: List[datetime],  # 날짜 리스트
        price: List[float],  # 가격(종가) 리스트
        low: List[float],  # 최저가 리스트
        high: List[float],  # 최고가 리스트
        tvol: List[float],  # 거래량 리스트
        tamt: List[float],  # 거래대금 리스트
    ):
        self.symbol = symbol
        self.exchange = exchange
        if not (
            len(date) == len(price) == len(low) == len(high) == len(tvol) == len(tamt)
        ):
            raise ValueError(
                "데이터의 길이가 일정하지 않습니다."
                f"date: {len(date)}, price: {len(price)}, low: {len(low)}, high: {len(high)}, tvol: {len(tvol)}, tamt: {len(tamt)}"
            )
        self.date = np.array(date)
        self.price = np.array(price)
        self.tvol = np.array(tvol)
        self.tamt = np.array(tamt)
        self.length = len(date)
        if self.length < 100:
            raise ValueError(f"데이터 길이는 100 이상이어야 합니다. 현재: {self.length}")

    def bollinger_band(self, period=20, multiplier=2):
        data = defaultdict(list)

        for i, price in enumerate(self.price[period:]):
            window = self.price[i : i + period]
            average = sum(window) / period
            std = sqrt(sum([(x - average) ** 2 for x in window]) / period)  # 표준편차
            upper = average + (std * multiplier)
            lower = average - (std * multiplier)
            perb = (price - lower) / (upper - lower)
            bandwidth = upper - lower / average

            data["center"].append(average)
            data["upper"].append(upper)
            data["lower"].append(lower)
            data["perb"].append(perb)
            data["bandwidth"].append(bandwidth)

        return dict(data)

    def __repr__(self) -> str:
        return f"<StockAnalyzer {self.symbol}/{self.exchange} (length: {self.length}, ref_date: {self.date[0]})>"
