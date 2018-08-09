#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from typing import List

class Stage(metaclass=ABCMeta):
    """
    Classes implementing this interface represent a stage in a computational process.

    `Stage` objects declare a precondition - if the precondition is true, it means that the stage can be executed and
    will not fail. `Stage` objects are intended to be chained together in `StageChain` objects, where executing a stage
    in the chain makes the precondition of the next stage true. In this way, the implicit postcondition of a stage is
    the precondition of the next stage.

    """

    @abstractmethod
    def name(self) -> str:
        """
        Returns the name of the stage.
        """
        pass

    @abstractmethod
    def check_precondition(self) -> bool:
        """
        Checks whether the precondition of this stage is satisfied. This method should not have any side effects.

        Returns:
            True if the precondition is satisfied; False otherwise.

        """
        pass

    @abstractmethod
    def execute(self) -> None:
        """
        Executes the stage.

        This operation is allowed (but not required) to fail if the precondition is not satisfied. Otherwise, the
        operation must not fail because of problems connected to the `StageChain` this `Stage` is a part of. Other kinds
        of failures are possible.

        The operation must not fail even in case the (implicit) postcondition is also true in addition to the
        precondition, for example if `execute` is called multiple times and that does not make the precondition false.

        """
        pass

class StageException(Exception):
    pass

class StageChain:
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
