# Simulation : Time Bomb, hasard ou stratégie ?

Ce module simule des parties de Time Bomb "à blanc" (sans discussion entre
joueurs) pour mesurer l'impact réel des choix faits à chaque "pince"
(quel joueur cibler, quelle carte de sa main révéler).

## Lancer la simulation

```bash
python -m back.run_simulation --games 5000
```

`--games` contrôle le nombre de parties simulées par configuration (plus il
y en a, plus les intervalles de confiance à 95% sont serrés).

## Stratégies disponibles (`back/src/strategies.py`)

### Stratégies "à l'aveugle" (information disponible dans le jeu réel)

- `random` : cible et carte tirées au hasard.
- `round_robin` : cible toujours le joueur suivant dans l'ordre de table.
- `max_hand_size` / `min_hand_size` : cible le joueur qui a le plus / le moins
  de cartes en main.
- `first_card` : cible un joueur au hasard mais révèle toujours sa première carte.

### Stratégies "oracle" (tricheuses, plafond théorique de skill)

- `oracle_sherlock` : voit la vraie identité de chaque carte et révèle en
  priorité DEFUSE > SECURE > BOMB.
- `oracle_moriarty` : voit la vraie identité de chaque carte et révèle en
  priorité BOMB > SECURE > DEFUSE.

Elles modélisent le cas où la discussion à table aurait parfaitement révélé
qui détient quoi — ce qui n'arrive jamais complètement en vrai, mais donne
une borne haute de ce que la "stratégie" peut apporter.

## Résultats (5000 parties / configuration, seed=42)

### 1) Stratégies à l'aveugle vs Moriarty aléatoire

| joueurs | random | round_robin | max_hand_size | min_hand_size | first_card |
|---|---|---|---|---|---|
| 4 | 14.7% | 13.6% | 15.6% | 13.5% | 14.9% |
| 5 | 10.5% | 11.3% | 11.0% | 10.3% | 10.5% |
| 6 |  7.8% |  8.3% |  7.5% |  9.0% |  8.2% |
| 7 |  6.3% |  6.8% |  5.5% |  6.2% |  5.8% |
| 8 |  4.6% |  4.2% |  4.2% |  4.9% |  4.4% |

(% de victoires Sherlock ; toutes les valeurs d'une même ligne se recoupent
dans leurs intervalles de confiance à 95%.)

### 2) Effet d'une information parfaite ("oracle")

| joueurs | random/random | oracle_sherlock/random | random/oracle_moriarty | oracle/oracle |
|---|---|---|---|---|
| 4 | 15.8% | 86.2% | 0.34% | 18.3% |
| 5 | 11.1% | 86.0% | 0.04% |  8.7% |
| 6 |  7.9% | 89.7% | 0.00% |  8.9% |
| 7 |  5.9% | 87.8% | 0.00% |  4.6% |
| 8 |  4.3% | 88.2% | 0.00% |  2.3% |

## Conclusions

1. **Sans information, le choix de cible/carte n'a aucun effet mesurable.**
   Toutes les stratégies "à l'aveugle" donnent le même taux de victoire que
   le hasard pur, à la marge d'erreur statistique près. C'est attendu : les
   cartes de chaque main sont rebattues à chaque manche, donc la position
   choisie (qui/où) est totalement décorrélée de la carte qui s'y trouve.
   **Mécaniquement, sans discussion à table, le jeu est 100% chance.**

2. **Le jeu mécanique favorise structurellement Moriarty, de plus en plus
   avec le nombre de joueurs** (Sherlock passe de ~15% de victoires à 4
   joueurs à ~4% à 8 joueurs en jeu aléatoire). Le vrai jeu compense ça par
   la discussion : les joueurs Sherlock doivent collectivement "déduire" qui
   a quoi pour viser juste, ce que le moteur ne modélise pas.

3. **L'information est ce qui crée le "skill".** Dès qu'on simule un joueur
   omniscient :
   - un Sherlock omniscient gagne ~86-90% des parties (il trouve les N
     cartes DEFUSE en quelques tours sans jamais révéler la bombe) ;
   - un Moriarty omniscient gagne quasiment 100% des parties en ~2.7 tours
     (il révèle la bombe dès qu'il en a l'occasion) ;
   - quand les deux camps sont omniscients, Moriarty garde l'avantage car
     "trouver LA bombe" est un objectif bien plus simple que "trouver les N
     cartes DEFUSE sans jamais tomber sur la bombe".

**Verdict** : la mécanique pure de "qui pince où" est entièrement due au
hasard. Tout le "skill" de Time Bomb vient de la discussion/bluff à table
(déduire qui sont les Moriarty et où se trouvent les cartes), un aspect que
ce moteur ne capture pas. Avec un plafond d'information parfaite, la partie
peut basculer à plus de 85% en faveur d'un camp — donc la discussion compte
énormément, mais le sous-jacent mécanique (sans elle) est purement aléatoire.
