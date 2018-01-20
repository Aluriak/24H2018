"""Strategy

Attempt to build DSLs for the specific problem.

See https://marabunta.haum.org


Methods:
- [x] ASP  (see run_ant_alt and run_nest)
- [x] Python interface (see run_ant)
- [ ] generalized ACCC + genetic algorithm
- [ ] model oriented ingeneering

"""

import os
import sys
import random
import itertools
from collections import namedtuple, defaultdict

import clyngor
import attr

Command = namedtuple('Command', 'type args')
Command.__new__.__defaults__ = (),
DIR = os.path.dirname(sys.argv[0])
ASP_ANT_FILES = (DIR + '/asp/ant.lp',)
ASP_NEST_FILES = (DIR + '/asp/nest.lp',)
LOGS = False
# LOGS = True

@attr.s
class Pheromone:
    idx = attr.ib(converter=int)
    zone = attr.ib()
    dist = attr.ib(converter=int)
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


def run_ant(commands:[Command]) -> [Command]:
    """Yield actions to send for given ant, knowing the input infos"""
    # build the DSL
    commands = tuple(commands)
    antype = int(next(c for c in commands if c.type == 'TYPE').args[0])
    stock = int(next(c for c in commands if c.type == 'STOCK').args[0])
    memory = list(map(int, next(c for c in commands if c.type == 'MEMORY').args))

    smap = itertools.starmap
    see = {
        'pheromone': tuple(smap(Pheromone, (c.args for c in commands if c.type == 'SEE_PHEROMONE'))),
        'food': tuple(smap(Food, (c.args for c in commands if c.type == 'SEE_FOOD'))),
        'nest': tuple(smap(Nest, (c.args for c in commands if c.type == 'SEE_NEST'))),
    }
    goto = lambda obj: Command('MOVE_TO', [obj.idx])
    foods = see['food']


    # use the DSL
    if antype == 1:  # explorer
        if memory[0] == 0:  # search for food
            if foods:  # drop a food pheromone, change memory accordingly
                yield Command('TURN', [180])
                memory[0], memory[1] = 1, 1  # food found
            else:  # no visible food: continue the searchs
                yield Command('EXPLORE')
        elif memory[0] == 1:  # food found ; go elsewhere
            if memory[1] == 1:  # pheromone already dropped
                yield Command('EXPLORE')
                memory[1] = 0
            elif memory[1] == 0:  # pheromone not dropped
                yield Command('PUT_PHEROMONE', [Pheromone.FOODPATH])
                memory[1] = 1

    elif antype == 2:  # scavenger
        memory[0] = 1 if stock >= 90 else 0
        if memory[0] == 0:  # search for food
            if foods:
                close_foods = tuple(p for p in foods if p.zone == 'NEAR' and p.amount > 1)
                if not any(p[1] == 'NEAR' for p in foods):  # nothing near
                    target = max(foods, key=lambda p: p.amount)
                    yield goto(target)
                else:  # something here
                    getfrom = random.choice(close_foods)
                    yield Command('COLLECT', (getfrom.idx, min(getfrom.amount-1, 100 - stock)))
            elif see.get('pheromone'):
                paths = tuple(p for p in see['pheromone'] if p.amount == Pheromone.FOODPATH)
                target = max(paths, key=lambda p: persistance)
                yield goto(target)
            else:
                yield Command('EXPLORE')
        else:  # goto nest
            friend_nests = tuple(n for n in see['nest'] if n.friend)
            if friend_nests:  # go to the closest
                target = min(friend_nests, key=lambda p: p.dist)
                yield goto(target)
            else:
                yield Command('EXPLORE')

    yield Command('SET_MEMORY', ' '.join(map(str, memory)))



def run_ant_alt(commands:[Command]) -> [Command]:
    yield from run_asp_solver(commands, ASP_ANT_FILES)


def run_nest(commands:[Command]) -> [Command]:
    """Yield actions to send for given nest, knowing the input infos"""
    yield from run_asp_solver(commands, ASP_NEST_FILES)


def run_asp_solver(commands:[Command], files:iter) -> [Command]:
    commands = tuple(commands)
    memory = list(next(c for c in commands if c.type == 'MEMORY').args)
    atoms = (''.join(
        '{}({}).'.format(type.lower(), ','.join(map(str.lower, map(str, args))))
        for type, args in commands)
        # + ''.join('memory({},{}).'.format(idx, mem)  # access to memory
                  # for idx, mem in enumerate(memory))
    )
    log('ASP ATOMS:', atoms)
    for model in clyngor.solve(files, inline=atoms).by_predicate:
        log('ASP MODEL:', model)
        for idx, increment in model.get('inc_memory', ()):
            memory[idx] = (int(memory[idx]) + increment) % 256
        for type, *args in model.get('do', ()):
            yield Command(type, tuple(args))
    yield Command('SET_MEMORY', memory)


def command_to_stdout(command:Command) -> print:
    assert command.type is not None
    print(command.type.upper(), ' '.join(map(str, command.args)))
def print_end() -> print:
    command_to_stdout(Command(CommandType.END))



def run_all():
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
            runner = globals()['run_' + state.lower()]
            for command in runner(commands):  # call the runner for received commands
                command_to_stdout(command)
            print_end()
            state, commands = None, []
        else:
            log('OTHER CMD:', command)
            assert state, state
            commands.append(command)


if __name__ == "__main__":
    run_all()
