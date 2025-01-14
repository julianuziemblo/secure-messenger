from dataclasses import dataclass
from enum import Enum
from typing import Callable


class Tui:
    def __init__(self):
        self.context = TuiContext()
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            ...


class TuiMode(Enum):
    Idle = 0
    Conversation = 1


@dataclass
class TuiCommand:
    name: str
    call_name = '/' + name
    modes: set[TuiMode]
    execute: Callable[[None], None]


class TuiContext:
    def __init__(self):
        self.state = TuiMode.idle

    @staticmethod
    def all_commands() -> set[TuiCommand]:
        return {
            TuiCommand('help', {TuiMode.Idle, TuiMode.Conversation}, lambda: print('Help used'))
        }

    def available_commands(self) -> set[TuiCommand]:
        ...
