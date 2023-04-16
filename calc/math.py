from math import sqrt
from typing import List
from datetime import datetime
from collections import defaultdict

import numpy as np


class StockAnalyzer:
    class InvalidParameter(Exception):
        """가진 데이터 크기보다 큰 파라미터가 입력된 경우 발생하는 예외 클래스"""

    def __init__(
        self,
        *,
        code: str,  # 종목코드
        exchange: str,  # 거래소코드
        date: List[datetime],  # 날짜 리스트
        price: List[float],  # 가격(종가) 리스트
        low: List[float],  # 최저가 리스트
        high: List[float],  # 최고가 리스트
        tvol: List[float],  # 거래량 리스트
        tamt: List[float],  # 거래대금 리스트
    ):
        self.code = code
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
        self.length = len(date)  # 0일 수 있음

    def bollinger_band(self, period=20, multiplier=2):
        """date, centor, upper, lower, perb, bandwidth"""
        if period > self.length:
            raise self.InvalidParameter

        data = defaultdict(list)

        for i, price in enumerate(self.price[period:], start=period):
            window = self.price[i - period : i]
            average = sum(window) / period
            std = sqrt(sum([(x - average) ** 2 for x in window]) / period)  # 표준편차
            upper = average + (std * multiplier)
            lower = average - (std * multiplier)
            perb = (price - lower) / (upper - lower)
            bandwidth = upper - lower / average

            data["date"].append(self.date[i])
            data["center"].append(average)
            data["upper"].append(upper)
            data["lower"].append(lower)
            data["perb"].append(perb)
            data["bandwidth"].append(bandwidth)

        return dict(data)

    def __repr__(self) -> str:
        return f"<calc.math.StockAnalyzer {self.code}/{self.exchange} (length: {self.length}, ref_date: {self.date[0]})>"

    def __bool__(self) -> bool:  # 가진 데이터가 없으면 이 객체는 False이다.
        return True if self.length else False
