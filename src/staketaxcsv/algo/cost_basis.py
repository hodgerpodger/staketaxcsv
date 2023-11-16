
from collections import deque
from decimal import Decimal
import logging
import math

from staketaxcsv.algo.asset import Asset


class Entry:
    def __init__(self, quantity: int, price: Decimal):
        if quantity == 0:
            raise ValueError("Invalid quantity")
        if price <= 0:
            raise ValueError("Invalid price")

        self.quantity = quantity
        self.price = price

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.price:.6f}"

    @property
    def size(self) -> int:
        return abs(self.quantity)

    @property
    def is_buy(self) -> bool:
        return self.quantity > 0

    @property
    def is_sell(self) -> bool:
        return self.quantity < 0

    @property
    def value(self) -> Decimal:
        return self.price * Decimal(self.size)

    def copy(self):
        return Entry(self.quantity, self.price)


class FIFO:
    def __init__(self, id: int):
        self._id = id
        self._balance = 0
        self._inventory = deque()
        self._history = []

    @property
    def balance(self) -> int:
        return self._balance

    def push(self, entry: Entry) -> Decimal:
        self._history.append(entry)
        if entry.is_buy:
            return self._buy(entry)
        elif entry.is_sell:
            return self._sell(entry)

    def _buy(self, entry: Entry) -> Decimal:
        self._balance += entry.size

        self._inventory.append(entry)

        return entry.value

    def _sell(self, entry: Entry) -> Decimal:
        size = entry.size
        if self._balance < size:
            logging.warning("Not enough balance in inventory to sell")
            self._balance = 0
            self._inventory.clear()
            return entry.value

        self._balance -= size
        remaining = size
        total_cost = Decimal(0)
        while remaining > 0:
            earliest = self._inventory.popleft().copy()
            if earliest.size >= remaining:
                earliest.quantity -= remaining

                if earliest.quantity > 0:
                    self._inventory.appendleft(earliest)

                total_cost += earliest.price * remaining
                remaining = 0
            else:
                total_cost += earliest.value
                remaining -= earliest.quantity

        return math.ceil(total_cost)


class DepositCostBasisTracker:
    def __init__(self):
        self.asset_cost_basis = {}

    def _get_asset_cost_basis_tracker(self, id) -> FIFO:
        if id not in self.asset_cost_basis:
            self.asset_cost_basis[id] = FIFO(id)
        return self.asset_cost_basis[id]

    def deposit(self, collateral: Asset, receipt: Asset):
        cost_basis = self._get_asset_cost_basis_tracker(receipt.id)
        exchange_rate = Decimal(collateral.uint_amount) / Decimal(receipt.uint_amount)
        cost_basis.push(Entry(receipt.uint_amount, exchange_rate))

    def withdraw(self, receipt: Asset, collateral: Asset) -> Asset:
        cost_basis = self._get_asset_cost_basis_tracker(receipt.id)
        exchange_rate = Decimal(collateral.uint_amount) / Decimal(receipt.uint_amount)
        cost = cost_basis.push(Entry(-receipt.uint_amount, exchange_rate))
        return Asset(collateral.id, max(collateral.uint_amount - cost, 0))
