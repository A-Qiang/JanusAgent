"""交易策略模块。"""

from dataclasses import dataclass


@dataclass
class Strategy:
    name: str
    description: str

    def run(self) -> None:
        raise NotImplementedError
