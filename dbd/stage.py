#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from typing import Dict, List, Optional

class Stage(metaclass=ABCMeta):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def check_precondition(self) -> bool:
        pass

    @abstractmethod
    def execute(self) -> None:
        pass

class StageException(Exception):
    pass

class StageExecutor:
    def __init__(self, stages: List[Stage]) -> None:
        # The first stage is executed first if there is no caching.
        self._stages = stages

    def execute_in_order(self) -> None:
        self._execute_in_order_from(0)

    def execute_needed(self) -> None:
        if len(self._stages) == 0:
            return

        index = len(self._stages) - 1
        while index > 0 and not self._stages[index].check_precondition():
            index -= 1

        # If index is not zero, we check its precondition twice, but accepting this makes the code simpler.
        self._execute_in_order_from(index)

    def _execute_in_order_from(self, start_index: int) -> None:
        for index in range(start_index, len(self._stages)):
            stage = self._stages[index]

            if not stage.check_precondition():
                raise StageException("The precondition of stage {} is not met.".format(stage.name()))

            stage.execute()
