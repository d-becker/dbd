#!/usr/bin/env python3

# pylint: disable=missing-docstring

import unittest

from typing import List

from stage import Stage, StageException, StageChain

class ListAppenderStage(Stage):
    def __init__(self, number: int, append_list: List[int]) -> None:
        self._number = number
        self._append_list = append_list

    def name(self) -> str:
        return str(self._number)

    def check_precondition(self) -> bool:
        return True

    def execute(self) -> None:
        self._append_list.append(self._number)

class PreconditionCheckingListAppenderStage(ListAppenderStage):
    def check_precondition(self) -> bool:
        return self._number == 0 or (self._number - 1) in self._append_list

class TestStageChain(unittest.TestCase):
    LIST_LENGTH = 10

    def test_execute_in_order_correct_order(self) -> None:
        append_list: List[int] = []
        stages = [ListAppenderStage(i, append_list) for i in range(TestStageChain.LIST_LENGTH)]

        stage_chain = StageChain(stages)
        stage_chain.execute_in_order()

        expected_list = [i for i in range(TestStageChain.LIST_LENGTH)]
        self.assertEqual(expected_list, append_list)

    def test_execute_in_order_unmet_precondition_raises(self) -> None:
        append_list: List[int] = []
        stages = [PreconditionCheckingListAppenderStage(i, append_list)
                  for i in reversed(range(TestStageChain.LIST_LENGTH))]

        stage_chain = StageChain(stages)

        with self.assertRaises(StageException):
            stage_chain.execute_in_order()

    def test_execute_in_order_empty_list_does_not_fail(self) -> None:
        stages: List[Stage] = []
        stage_chain = StageChain(stages)
        stage_chain.execute_in_order()

    def test_execute_needed_correct_stages_executed(self) -> None:
        append_list = [i for i in range(int(TestStageChain.LIST_LENGTH / 2))]

        stages = [PreconditionCheckingListAppenderStage(i, append_list)
                  for i in range(TestStageChain.LIST_LENGTH)]

        stage_chain = StageChain(stages)
        stage_chain.execute_needed()

        # If unneeded stages are executed, there will be duplicates in append_list.
        # If some needed stages are not executed, there will be missing elements in append_list.
        # Therefore, the lists will only be equal if exactly the needed stages are executed.
        expected_list = [i for i in range(TestStageChain.LIST_LENGTH)]
        self.assertEqual(expected_list, append_list)

    def test_execute_needed_no_precondition_is_met(self) -> None:
        append_list: List[int] = []
        stages = [PreconditionCheckingListAppenderStage(i, append_list)
                  for i in range(1, TestStageChain.LIST_LENGTH + 1)]

        stage_chain = StageChain(stages)
        with self.assertRaises(StageException):
            stage_chain.execute_needed()

    def test_execute_needed_empty_list_does_not_fail(self) -> None:
        stages: List[Stage] = []
        stage_chain = StageChain(stages)
        stage_chain.execute_needed()
