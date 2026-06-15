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
- `InformedMoriartyStrategy(lie_rate)` : si le détenteur de la bombe est connu,
  il devient la cible prioritaire (carte au hasard dans sa main). Un Moriarty
  qui a la bombe l'annonce avec une probabilité `(1 - lie_rate)` (sinon il "ne
  dit pas qu'il a Big Ben"). Il n'y a aucun canal privé côté Moriarty : un
  Moriarty qui cache la bombe la cache à tout le monde, y compris ses propres
  coéquipiers.

Ces deux stratégies sont appariées (même `lie_rate`) : c'est la même annonce
publique que tout le monde entend.

### Stratégies "annonce de DEFUSE" (un indice public par manche : qui a combien de DEFUSE)

Au début de chaque manche, chaque joueur annonce publiquement combien de
cartes DEFUSE il a en main (`GameState.claimed_defuse`, voir
`back/src/simulation.py`). Les Sherlock annoncent toujours leur vrai compte.
Les Moriarty peuvent surenchérir de `moriarty_bluff` cartes (plafonné à la
taille de leur main) pour se faire passer pour des Sherlock bien fournis.

- `DefuseAnnouncementStrategy` (`defuse_announcement`) : cible toujours le
  joueur qui a annoncé le plus de DEFUSE (carte au hasard dans sa main).
- `TrustWeightedStrategy` (`trust_weighted`) : cible le joueur dont
  `claimed_defuse x trust` est le plus élevé. Le score de `trust` d'un joueur
  (initialisé à 1.0) est divisé par deux dès qu'il est pris en flagrant délit
  de mensonge : soit parce qu'une carte DEFUSE de plus que son annonce a été
  révélée de sa main, soit parce que sa main a été entièrement vidée sans que
  le compte de DEFUSE révélées corresponde à son annonce.

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

Pas de canal privé : un Moriarty qui cache la bombe la cache à tout le monde,
y compris ses propres coéquipiers.

| joueurs | lie=0.00 | lie=0.25 | lie=0.50 | lie=0.75 | lie=1.00 |
|---|---|---|---|---|---|
| 4 | 12.0% | 11.7% | 11.6% | 10.6% | 10.4% |
| 5 |  4.4% |  4.4% |  4.6% |  5.2% |  4.6% |
| 6 |  2.6% |  3.4% |  2.6% |  2.8% |  2.7% |
| 7 |  1.0% |  1.1% |  1.4% |  1.4% |  1.7% |
| 8 |  0.4% |  0.3% |  0.5% |  0.9% |  0.9% |

(% de victoires Sherlock, `lie` = probabilité qu'un Moriarty cache qu'il a la
bombe. À comparer à la ligne random/random de la table 2 : 15.8% / 11.1% /
7.9% / 5.9% / 4.3%.)

### 4) "On en parle à table" : annonce du nombre de DEFUSE en main

Au début de chaque manche, chaque joueur annonce son nombre de DEFUSE.
Sherlock annonce toujours la vérité. Moriarty annonce `vrai + bluff` (plafonné
à sa taille de main). Moriarty cible au hasard (`random`) dans tous les cas ;
seule la stratégie côté Sherlock change.

#### bluff=0 (Moriarty annonce honnêtement)

| joueurs | random | defuse_announcement | trust_weighted |
|---|---|---|---|
| 4 | 14.5% | 38.4% | 38.4% |
| 5 | 12.4% | 40.8% | 42.0% |
| 6 |  7.7% | 47.0% | 47.2% |
| 7 |  6.5% | 47.4% | 47.8% |
| 8 |  4.6% | 49.1% | 48.8% |

#### bluff=1

| joueurs | random | defuse_announcement | trust_weighted |
|---|---|---|---|
| 4 | 15.9% | 29.0% | 28.8% |
| 5 | 11.7% | 27.9% | 27.9% |
| 6 |  8.6% | 28.1% | 28.9% |
| 7 |  6.5% | 25.8% | 26.7% |
| 8 |  4.1% | 26.1% | 27.1% |

#### bluff=2

| joueurs | random | defuse_announcement | trust_weighted |
|---|---|---|---|
| 4 | 15.2% | 19.3% | 18.9% |
| 5 | 11.1% | 18.0% | 17.7% |
| 6 |  8.2% | 14.4% | 15.6% |
| 7 |  6.4% | 12.2% | 14.4% |
| 8 |  4.5% | 10.0% | 12.0% |

#### bluff=3

| joueurs | random | defuse_announcement | trust_weighted |
|---|---|---|---|
| 4 | 15.1% | 16.8% | 17.0% |
| 5 | 11.1% | 12.8% | 14.2% |
| 6 |  7.8% | 10.1% | 11.2% |
| 7 |  5.9% |  9.0% |  9.6% |
| 8 |  4.4% |  7.6% |  7.9% |

(% de victoires Sherlock ; `bluff` = nombre de DEFUSE qu'un Moriarty
sur-annonce par rapport à son vrai compte.)

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
   Sherlock — et reste pire pour Sherlock que le hasard pur, quel que soit
   `lie`.** Avec l'annonce de la bombe (table 3), Sherlock reste autour de
   10-12% à 4 joueurs et sous 1% à 8 joueurs, contre ~15.8%/4.3% en hasard pur
   (table 2, random/random) — et faire varier `lie` de 0 à 1 ne suffit pas à
   revenir au niveau du hasard pur. Pourquoi : "éviter" le détenteur connu de
   la bombe n'aide pas Sherlock à trouver ses N cartes DEFUSE (qui sont
   ailleurs sur la table), alors que ce même indice permet à Moriarty de
   foncer beaucoup plus souvent sur le bon joueur pour faire sortir la bombe.

5. **L'annonce du nombre de DEFUSE, elle, profite nettement à Sherlock — et
   c'est le premier indice de cette simulation qui l'avantage.** Avec
   `defuse_announcement`/`trust_weighted` et des Moriarty honnêtes (table 4,
   bluff=0), le taux de victoire de Sherlock est multiplié par 2.5 à 10 selon
   le nombre de joueurs (ex. 4.6% → ~49% à 8 joueurs). Contrairement à
   l'indice "qui a la bombe" (qui pointe directement vers l'unique objectif de
   Moriarty), savoir "qui a le plus de DEFUSE" pointe directement vers
   l'objectif de Sherlock. Mentir efface vite cet avantage : dès que les
   Moriarty sur-annoncent de 1 à 3 cartes (bluff=1 à 3), le gain fond
   rapidement (à bluff=3, Sherlock reste au-dessus du hasard mais de
   seulement quelques points). Le score de `trust` (qui démasque un menteur
   pris en flagrant délit) apporte un léger supplément par rapport à
   `defuse_announcement` seul, surtout aux `bluff` élevés, mais ne suffit pas
   à restaurer l'avantage initial : une seule "prise sur le fait" par partie
   ne compense pas des annonces mensongères répétées à chaque manche.

**Verdict** : la mécanique pure de "qui pince où" est entièrement due au
hasard. Tout le "skill" de Time Bomb vient de la discussion/bluff à table
(déduire qui sont les Moriarty et où se trouvent les cartes), un aspect que
ce moteur ne capture qu'au travers des indices simulés. Le plafond
d'information parfaite est énorme (+85 points pour Sherlock, quasi 100% pour
Moriarty), mais tous les indices "réalistes" ne se valent pas : un indice
qui pointe vers l'objectif de Moriarty (où est la bombe) profite à Moriarty
même quand il est imparfait ou mensonger, alors qu'un indice qui pointe vers
l'objectif de Sherlock (qui a des DEFUSE) profite réellement à Sherlock,
tant que le mensonge des Moriarty reste limité. La discussion à table n'est
donc bonne pour les "gentils" que si elle porte sur *leurs* indices, pas sur
ceux de Moriarty — et son effet s'érode vite face au bluff.
