from __future__ import annotations

from abc import ABC, abstractmethod

from src.models import Document, ProductConfig


class Collector(ABC):
    source_type: str

    @abstractmethod
    def collect(self, product: ProductConfig, start_date: str, end_date: str) -> list[Document]:
        raise NotImplementedError

