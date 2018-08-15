#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import List

class Stage(metaclass=ABCMeta):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def execute(self, input_path: Path, output_path: Path) -> None:
        pass

class EntryStage(metaclass=ABCMeta):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def execute(self, output_path: Path) -> None:
        pass

class FinalStage(metaclass=ABCMeta):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def execute(self, input_path: Path) -> None:
        pass

class Pipeline:
    def __init__(self,
                 entry_stage: EntryStage,
                 inner_stages: List[Stage],
                 final_stage: FinalStage) -> None:
        self.entry_stage = entry_stage
        self.inner_stages = inner_stages
        self.final_stage = final_stage
