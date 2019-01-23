#!/usr/bin/env python3

"""
This module contains the main building blocks of the pipeline package. For more information, see the package level
documentation.
"""

from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import List

class Stage(metaclass=ABCMeta):
    """
    An interface representing a stage the input and output of which are both files.
    These are the inner stages of filesystem-cached pipelines.
    """

    @abstractmethod
    def name(self) -> str:
        """
        Returns the name of the stage.
        """
        pass

    @abstractmethod
    def execute(self, input_path: Path, output_path: Path) -> None:
        """
        Executes the stage using the given input and output paths.

        Args:
            input_path: The path to the input file.
            output_path: The path to the output file.
        """
        pass

class EntryStage(metaclass=ABCMeta):
    """
    An interface representing a stage the output of which is a file.
    An `EntryStage` is the first stage of a filesystem-cached pipeline.
    """

    @abstractmethod
    def name(self) -> str:
        """
        Returns the name of the stage.
        """
        pass

    @abstractmethod
    def execute(self, output_path: Path) -> None:
        """
        Executes the entry stage using the given output path.

        Args:
            output_path: The path to the output file.
        """
        pass

class FinalStage(metaclass=ABCMeta):
    """
    An interface representing a stage the input of which is a file.
    A `FinalStage` is the last stage of a filesystem-cached pipeline.
    """

    @abstractmethod
    def name(self) -> str:
        """
        Returns the name of the stage.
        """
        pass

    @abstractmethod
    def execute(self, input_path: Path) -> None:
        """
        Executes the final stage using the given input path.

        Args:
            input_path: The path to the input file.
        """
        pass

    @abstractmethod
    def postcondition_satisfied(self) -> bool:
        """
        Checks whether the postcondition of the stage is satisfied.
        For other kinds of stages, this can be done by checking if the
        output file exists, but `FinalStage`s do not have output files.

        Returns:
            `True` if the postcondition is satisfied; `False` otherwise.
        """
        pass

class Pipeline:
    """
    A class representing a pipeline of stages. It is composed of an `EntryStage`, a list of `Stage`s and a `FinalStage`.
    """

    def __init__(self,
                 entry_stage: EntryStage,
                 inner_stages: List[Stage],
                 final_stage: FinalStage) -> None:
        """
        Creates a new `Pipiline` object.

        Args:
            entry_stage: The entry stage of the pipeline.
            inner_stages: The inner stages of the pipeline.
            final_stage: The final stage of the pipeline.
        """

        self.entry_stage = entry_stage
        self.inner_stages = inner_stages
        self.final_stage = final_stage
