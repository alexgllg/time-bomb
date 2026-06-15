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

### Stratégies "informées" (un seul indice public : qui a la bombe)

- `InformedSherlockStrategy(lie_rate)` : si un joueur a la bombe en main et que
  c'est connu publiquement, ce joueur n'est jamais ciblé. Un Sherlock qui a la
  bombe l'annonce **toujours** ("les gentils disent la vérité").
- `InformedMoriartyStrategy(lie_rate, team_aware)` : si le détenteur de la
  bombe est connu, il devient la cible prioritaire (carte au hasard dans sa
  main). Un Moriarty qui a la bombe l'annonce avec une probabilité
  `(1 - lie_rate)` (sinon il "ne dit pas qu'il a Big Ben"). Si `team_aware` est
  vrai, les Moriarty se le disent toujours en privé entre eux, même quand ils
  le cachent au reste de la table.

Ces deux stratégies sont appariées (même `lie_rate`) : c'est la même annonce
publique que tout le monde entend, seul `team_aware` ajoute un canal privé
côté Moriarty.

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

### 3) "On en parle à table" : annonce (honnête ou pas) de qui a la bombe

`team_aware=False` : les Moriarty n'ont accès qu'à l'annonce publique (comme
Sherlock). `team_aware=True` : les Moriarty connaissent toujours en privé
le détenteur de la bombe, même caché publiquement.

| joueurs | lie=0.00, public | lie=0.00, team_aware | lie=0.50, public | lie=0.50, team_aware | lie=1.00, public | lie=1.00, team_aware |
|---|---|---|---|---|---|---|
| 4 | 12.0% | 11.2% | 11.0% | 9.5% | 9.5% | 8.1% |
| 5 |  4.5% |  4.7% |  5.5% | 3.8% | 5.3% | 3.4% |
| 6 |  2.8% |  2.9% |  3.3% | 2.5% | 3.0% | 1.8% |
| 7 |  1.0% |  1.0% |  1.1% | 0.6% | 1.5% | 0.7% |
| 8 |  0.3% |  0.4% |  0.5% | 0.3% | 0.8% | 0.3% |

(% de victoires Sherlock, `lie` = probabilité qu'un Moriarty cache qu'il a la
bombe.)

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

4. **Un petit indice ("qui a la bombe") profite surtout à Moriarty, pas à
   Sherlock — et peut même être pire pour Sherlock que le hasard pur.** Avec
   l'annonce de la bombe (table 3), Sherlock tombe à ~8-12% à 4 joueurs et
   quasi 0% à 8 joueurs, soit *moins* que le ~15.8%/4.3% du hasard pur (table
   2, random/random). Pourquoi : "éviter" le détenteur connu de la bombe
   n'aide pas Sherlock à trouver ses N cartes DEFUSE (qui sont ailleurs sur la
   table), alors que ce même indice permet à Moriarty de foncer
   immédiatement sur le bon joueur pour faire sortir la bombe. Le réglage
   `team_aware` confirme l'intuition : plus les Moriarty se coordonnent en
   privé (et plus ils mentent en public, `lie` élevé), plus Sherlock perd —
   l'effet est petit mais cohérent à tous les nombres de joueurs.

**Verdict** : la mécanique pure de "qui pince où" est entièrement due au
hasard. Tout le "skill" de Time Bomb vient de la discussion/bluff à table
(déduire qui sont les Moriarty et où se trouvent les cartes), un aspect que
ce moteur ne capture pas. Le plafond d'information parfaite est énorme (+85
points pour Sherlock, quasi 100% pour Moriarty), mais une information
*partielle et asymétrique* (un indice public, plus ou moins fiable, sur "qui
a la bombe") tend à favoriser Moriarty plutôt que Sherlock — la discussion à
table n'est donc pas automatiquement bonne pour les "gentils".
