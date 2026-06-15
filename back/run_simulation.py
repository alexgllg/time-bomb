"""Run a battery of Time Bomb simulations to estimate how much of the game
is decided by luck vs. by the choices made at each pinch.

Usage:
    python -m back.run_simulation [--games 5000] [--seed 42]
"""
import argparse
import random

from back.src import strategies as strat
from back.src.simulation import run_experiment

PLAYER_COUNTS = range(4, 9)


def _print_table(rows, headers):
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    fmt = ' | '.join('{:<' + str(w) + '}' for w in widths)
    print(fmt.format(*headers))
    print('-+-'.join('-' * w for w in widths))
    for row in rows:
        print(fmt.format(*row))


def _format_result(res):
    lo, hi = res['sherlock_win_rate_ci']
    return (
        str(res['n_players']),
        res['sherlock_strategy'],
        res['moriarty_strategy'],
        f"{res['sherlock_win_rate'] * 100:5.2f}%",
        f"[{lo * 100:5.2f}%, {hi * 100:5.2f}%]",
        f"{res['avg_pinches']:.2f}",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--games', type=int, default=5000, help='games per configuration')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    headers = ('joueurs', 'Sherlock', 'Moriarty', '% victoire Sherlock', 'IC 95%', 'tours moy.')

    print('=== 1) Stratégies "à l\'aveugle" (aucune information sur les cartes) vs Moriarty aléatoire ===')
    print('Le but est de voir si une heuristique plus "maline" qu\'un tirage au hasard change le taux de victoire.\n')
    rows = []
    for n in PLAYER_COUNTS:
        for blind in strat.BLIND_STRATEGIES:
            res = run_experiment(n, blind, strat.RANDOM, args.games)
            rows.append(_format_result(res))
    _print_table(rows, headers)

    print('\n=== 2) Effet d\'une information parfaite ("oracle") sur les cartes ===')
    print('L\'oracle voit la vraie identité de chaque carte avant de la révéler : il modélise le plafond de')
    print('"skill" atteignable si la discussion à table révélait parfaitement qui a quoi.\n')
    matchups = [
        (strat.RANDOM, strat.RANDOM),
        (strat.ORACLE_SHERLOCK, strat.RANDOM),
        (strat.RANDOM, strat.ORACLE_MORIARTY),
        (strat.ORACLE_SHERLOCK, strat.ORACLE_MORIARTY),
    ]
    rows = []
    for n in PLAYER_COUNTS:
        for sherlock_strategy, moriarty_strategy in matchups:
            res = run_experiment(n, sherlock_strategy, moriarty_strategy, args.games)
            rows.append(_format_result(res))
    _print_table(rows, headers)


if __name__ == '__main__':
    main()
