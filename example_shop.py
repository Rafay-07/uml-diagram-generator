"""Sample domain used by the README and tests: a tiny order-processing model."""
from abc import ABC, abstractmethod


class Payment(ABC):
    @abstractmethod
    def charge(self, amount: float) -> bool: ...


class CardPayment(Payment):
    def __init__(self, last4: str):
        self.last4: str = last4

    def charge(self, amount: float) -> bool:
        return amount > 0


class Item:
    def __init__(self, name: str, price: float):
        self.name: str = name
        self.price: float = price


class Order:
    def __init__(self, payment: Payment):
        self.payment: Payment = payment
        self.items: list[Item] = []
        self._paid: bool = False

    def add(self, item: Item) -> None:
        self.items.append(item)

    def total(self) -> float:
        return sum(i.price for i in self.items)

    def checkout(self) -> bool:
        self._paid = self.payment.charge(self.total())
        return self._paid
