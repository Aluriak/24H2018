"""Strategy

Attempt to build DSLs for the specific problem.

See https://marabunta.haum.org


Methods:
- [x] ASP  (see run_ant_alt and run_nest)
- [x] Python interface (see run_ant and run_ant_by_state)
- [ ] generalized ACCC + genetic algorithm
- [ ] model oriented ingeneering

"""

import os
import sys
import random
import itertools

import clyngor
import attr

from utils import Command, Pheromone, Food, Nest, log, run_all


DIR = os.path.dirname(sys.argv[0])
ASP_ANT_FILES = (DIR + '/asp/ant.lp',)
ASP_NEST_FILES = (DIR + '/asp/nest.lp',)

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
    pheromones = see['pheromone']


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
                if not any(p.zone == 'NEAR' for p in foods):  # nothing near
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


def run_ant_by_state(commands):
    # TODO: include DSL of run_ant
    # determine the state
    state = frozenset(state for state, ok in {
        'explorer searching for food': antype == 1 and memory[0] == 0 and not foods,
        'explorer finding food': antype == 1 and memory[0] == 0 and foods,
        'explorer going home': antype == 1 and memory[0] == 1 and memory[1] == 1,
        'explorer marking path': antype == 1 and memory[0] == 1 and memory[1] == 0,
        'scavenger searching for food (lost)': antype == 2 and memory[0] == 0 and not food and not pheromones,
        'scavenger searching for food (following marks)': antype == 2 and memory[0] == 0 and not food and pheromones,
        'scavenger finding food': antype == 2 and memory[0] == 0 and food,
        'scavenger going home': antype == 2 and memory[0] == 1 and memory[1] == 1,  # should be divided into multiple states to catch unconsistent cases
    }.items() if ok)
    assert len(state) == 1


    if state == 'explorer searching for food':
        yield Command('EXPLORE')
    if state == 'explorer finding food':
        yield Command('TURN', [180])
        memory[0], memory[1] = 1, 1  # food found
    if state == 'explorer going home':
        yield Command('EXPLORE')
        memory[1] = 0
    if state == 'explorer marking path':
        yield Command('PUT_PHEROMONE', [Pheromone.FOODPATH])
        memory[1] = 1
    if state == 'scavenger finding food':
        close_foods = tuple(p for p in foods if p.zone == 'NEAR' and p.amount > 1)
        if not any(p.zone == 'NEAR' for p in foods):  # nothing near
            target = max(foods, key=lambda p: p.amount)
            yield goto(target)
        else:  # something here
            getfrom = random.choice(close_foods)
            yield Command('COLLECT', (getfrom.idx, min(getfrom.amount-1, 100 - stock)))
    if state == 'scavenger searching for food (lost)':
        yield Command('EXPLORE')
    if state == 'scavenger searching for food (following marks)':
        paths = tuple(p for p in see['pheromone'] if p.amount == Pheromone.FOODPATH)
        target = max(paths, key=lambda p: persistance)
        yield goto(target)
    if state == 'scavenger going home':
        friend_nests = tuple(n for n in see['nest'] if n.friend)
        if friend_nests:  # go to the closest
            target = min(friend_nests, key=lambda p: p.dist)
            yield goto(target)
        else:
            yield Command('EXPLORE')


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




if __name__ == "__main__":
    run_all({'ant': run_ant, 'nest': run_nest})
