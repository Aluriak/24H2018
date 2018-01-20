"""Contains general purpose functions"""

import attr
from collections import namedtuple, defaultdict

LOGS = False
# LOGS = True

Command = namedtuple('Command', 'type args')
Command.__new__.__defaults__ = (),


@attr.s
class Pheromone:
    idx = attr.ib(converter=int)
    zone = attr.ib()
    dist = attr.ib(converter=int)
    type = attr.ib(converter=int)
    persistance = attr.ib(converter=int)
    FOODPATH = 1
@attr.s
class Food:
    idx = attr.ib(converter=int)
    zone = attr.ib()
    dist = attr.ib(converter=int)
    amount = attr.ib(converter=int)
@attr.s
class Nest:
    idx = attr.ib(converter=int)
    zone = attr.ib()
    dist = attr.ib(converter=int)
    friend = attr.ib(converter=lambda v: v == 'FRIEND')


class CommandType:
    BEGIN = 'BEGIN'
    END = 'END'

class NEST:
    INFO = {'STOCK', 'MEMORY', 'ANT_COUNT', 'ANT_IN'}
    ACTIONS = {'ANT_NEW', 'ANT_OUT', 'SET_MEMORY'}

class ANT:
    INFO = {'TYPE', 'MEMORY', 'ATTACKED', 'STAMINA', 'STOCK', 'SEE_PHEROMONE',
            'SEE_NEST', 'SEE_ANT', 'SEE_FOOD'}
    ACTIONS = {'EXPLORE', 'TURN', 'MOVE_TO', 'PUT_PHEROMONE', 'CHANGE_PHEROMONE',
               'COLLECT', 'DO_TROPHALLAXIS', 'EAT', 'NEST', 'ATTACK',
               'SUICIDE', 'SET_MEMORY'}


def log(*msg, **opts) -> print:
    """If logs are enabled, print given parameters as comments"""
    if LOGS:
        print(':', *msg, **opts)


def stdin() -> [str]:
    """Yield line found in input until a END is found. END itself is send."""
    while True:
        try:
            line = input().strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line.strip(): continue  # ignore empty lines
        # log('STDIN:', line[:14])
        yield line


def read_commands() -> [Command]:
    """Yield command found in input until END command"""
    for line in stdin():
        if line.startswith(('#', ': ')): continue  # comment
        line = line.split()
        # log('LINE:', line)
        com = Command(line[0], (line[1:] if len(line) > 1 else ()))
        # log('WSOZXJ:', line, com)
        yield com


def command_to_stdout(command:Command) -> print:
    assert command.type is not None
    print(command.type.upper(), ' '.join(map(str, command.args)))
def print_end() -> print:
    command_to_stdout(Command(CommandType.END))



def run_all(runners:dict):
    """Operate I/O"""
    state = None  # either NEST or ANT
    commands = []  # contains all commands for one agent

    for command in read_commands():
        if command.type == CommandType.BEGIN:
            log('BEGIN CMD:', command)
            assert len(command.args) == 1
            state = command.args[0]
        elif command.type == CommandType.END:
            if state is None:
                log('WHOLOLO: no state when receiving END command.')
            log('END CMD:', command)
            assert len(command.args) == 0
            runner = runners[state.lower()]
            for command in runner(commands):  # call the runner for received commands
                command_to_stdout(command)
            print_end()
            state, commands = None, []
        else:
            log('OTHER CMD:', command)
            assert state, state
            commands.append(command)
