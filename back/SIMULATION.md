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
Les Moriarty décalent leur annonce de `moriarty_bluff` cartes (plafonné entre
0 et la taille de leur main) :

- `moriarty_bluff > 0` : ils **sur-annoncent** pour se faire passer pour de
  gros porteurs de DEFUSE (et attirer les pinces sur eux).
- `moriarty_bluff < 0` : ils **sous-annoncent** pour cacher les DEFUSE qu'ils
  ont réellement et éviter d'être pinchés là où ça compte.

- `DefuseAnnouncementStrategy` (`defuse_announcement`) : cible toujours le
  joueur qui a annoncé le plus de DEFUSE (carte au hasard dans sa main).
- `TrustWeightedStrategy` (`trust_weighted`) : cible le joueur dont
  `claimed_defuse x trust` est le plus élevé. Le score de `trust` d'un joueur
  (initialisé à 1.0) est divisé par deux dès qu'il est pris en flagrant délit
  de mensonge : soit parce qu'une carte DEFUSE de plus que son annonce a été
  révélée de sa main, soit parce que sa main a été entièrement vidée sans que
  le compte de DEFUSE révélées corresponde à son annonce.
- `SuspicionWeightedStrategy` (`suspicion_weighted`) : va plus loin que
  `trust_weighted`. Pour un joueur jamais pris (`trust == 1`), le score est
  identique à `claimed_defuse`. Pour un joueur déjà pris en flagrant délit
  (`trust < 1`), son annonce n'est plus fiable : le score mélange l'annonce
  et la taille de sa main restante, sur l'hypothèse qu'un menteur démasqué
  pourrait cacher jusqu'à une main pleine de DEFUSE - même s'il a annoncé 0.

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

Au début de chaque manche, chaque joueur annonce son nombre de DEFUSE
(`claimed_defuse`). Sherlock annonce toujours la vérité. Moriarty décale son
annonce de `moriarty_bluff` cartes, plafonné entre 0 et sa taille de main :

- `bluff < 0` (sous-annonce) : "je n'ai pas de DEFUSE, ne me pinchez pas" —
  cache les DEFUSE réellement détenus.
- `bluff > 0` (sur-annonce) : "j'ai plein de DEFUSE, pinchez-moi" — se fait
  passer pour une cible juteuse alors qu'il en a moins.

Moriarty cible au hasard (`random`) dans tous les cas ; seule la stratégie
côté Sherlock change.

#### Taux de victoire Sherlock par nombre de joueurs

##### 4 joueurs

| bluff | random | defuse_announcement | trust_weighted | suspicion_weighted |
|---|---|---|---|---|
| -3 | 14.7% | 30.3% | 30.0% | 29.5% |
| -2 | 14.9% | 31.3% | 30.9% | 28.6% |
| -1 | 14.3% | 33.1% | 33.4% | 33.2% |
|  0 | 14.9% | 38.5% | 38.1% | 38.8% |
| +1 | 15.1% | 28.2% | 28.3% | 29.0% |
| +2 | 15.7% | 19.2% | 19.1% | 20.0% |
| +3 | 14.8% | 16.1% | 16.4% | 17.0% |

##### 5 joueurs

| bluff | random | defuse_announcement | trust_weighted | suspicion_weighted |
|---|---|---|---|---|
| -3 | 10.4% | 32.9% | 32.9% | 31.2% |
| -2 | 11.2% | 34.7% | 33.4% | 32.7% |
| -1 | 11.7% | 37.2% | 36.4% | 34.8% |
|  0 | 11.3% | 41.7% | 41.6% | 41.3% |
| +1 | 11.0% | 26.9% | 27.7% | 27.5% |
| +2 | 10.9% | 17.4% | 17.6% | 17.2% |
| +3 | 10.9% | 13.8% | 13.0% | 14.6% |

##### 6 joueurs

| bluff | random | defuse_announcement | trust_weighted | suspicion_weighted |
|---|---|---|---|---|
| -3 |  7.8% | 40.7% | 41.1% | 39.5% |
| -2 |  7.3% | 41.2% | 41.0% | 39.4% |
| -1 |  8.1% | 41.8% | 44.4% | 41.3% |
|  0 |  8.8% | 47.1% | 47.5% | 47.2% |
| +1 |  8.4% | 27.5% | 28.6% | 27.6% |
| +2 |  8.5% | 15.0% | 15.3% | 13.8% |
| +3 |  8.3% |  9.9% | 10.7% | 10.7% |

##### 7 joueurs

| bluff | random | defuse_announcement | trust_weighted | suspicion_weighted |
|---|---|---|---|---|
| -3 |  6.2% | 39.5% | 38.8% | 38.1% |
| -2 |  5.5% | 39.9% | 39.8% | 37.9% |
| -1 |  6.3% | 41.3% | 40.1% | 37.9% |
|  0 |  6.3% | 46.9% | 48.4% | 46.5% |
| +1 |  6.0% | 26.2% | 29.3% | 25.7% |
| +2 |  6.7% | 12.1% | 14.3% | 12.9% |
| +3 |  5.9% |  8.8% |  9.7% |  9.2% |

##### 8 joueurs

| bluff | random | defuse_announcement | trust_weighted | suspicion_weighted |
|---|---|---|---|---|
| -3 |  4.7% | 39.0% | 39.9% | 39.6% |
| -2 |  4.2% | 39.3% | 39.0% | 39.2% |
| -1 |  4.7% | 42.5% | 43.1% | 40.5% |
|  0 |  4.5% | 48.6% | 49.6% | 48.7% |
| +1 |  4.3% | 26.3% | 27.2% | 23.8% |
| +2 |  4.3% | 11.4% | 11.1% | 11.5% |
| +3 |  4.6% |  7.2% |  8.3% |  7.2% |

(% de victoires Sherlock ; `bluff` = décalage signé entre l'annonce de DEFUSE
d'un Moriarty et son vrai compte, plafonné entre 0 et sa taille de main.
`bluff = 0` = annonce honnête.)

#### Pourquoi la partie se termine : bombe révélée vs. timeout

Pour comprendre l'effet du bluff sur la victoire de Moriarty, voici comment
se terminent les parties Sherlock=`trust_weighted` / Moriarty=`random`, pour
trois valeurs de `bluff` (sous-annonce maximale, honnête, sur-annonce
maximale) :

| joueurs | bluff=-3 : % bombe / % timeout | bluff=0 : % bombe / % timeout | bluff=+3 : % bombe / % timeout |
|---|---|---|---|
| 4 | 64.6% / 5.3% | 59.1% / 2.8% | 72.6% / 11.0% |
| 5 | 62.0% / 5.1% | 56.7% / 1.7% | 74.7% / 12.3% |
| 6 | 55.9% / 3.0% | 51.9% / 0.6% | 75.8% / 13.5% |
| 7 | 57.3% / 3.9% | 50.7% / 0.9% | 75.6% / 14.7% |
| 8 | 56.4% / 3.7% | 50.0% / 0.4% | 75.7% / 16.0% |

(le reste jusqu'à 100% correspond aux victoires Sherlock par
`defuse_complete` — les 4 DEFUSE trouvées avant la fin de la 4e manche.)

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
   `defuse_announcement`/`trust_weighted`/`suspicion_weighted` et des Moriarty
   honnêtes (table 4, bluff=0), le taux de victoire de Sherlock est multiplié
   par 2.5 à 10 selon le nombre de joueurs (ex. 4.5% → ~48-50% à 8 joueurs).
   Contrairement à l'indice "qui a la bombe" (qui pointe directement vers
   l'unique objectif de Moriarty), savoir "qui a le plus de DEFUSE" pointe
   directement vers l'objectif de Sherlock. Mais cet avantage est fragile :
   **`bluff=0` (annonce honnête) est le pic absolu pour Sherlock, quel que
   soit le nombre de joueurs** — toute déviation de l'annonce de Moriarty,
   dans un sens ou dans l'autre, fait baisser le taux de victoire de Sherlock
   par rapport à ce pic.

6. **Les deux sens du mensonge ne sont pas équivalents : sur-annoncer détruit
   presque tout l'avantage de Sherlock, alors que sous-annoncer ne l'érode
   que partiellement.** À `bluff=+3` ("j'ai plein de DEFUSE, pinchez-moi"),
   Sherlock retombe proche de son niveau aléatoire (ex. à 8 joueurs : 49.6% à
   bluff=0 contre seulement 8.3% à bluff=+3, pour 4.5% en `random`/`random`
   pur). À `bluff=-3` ("je n'ai rien, ne me pinchez pas"), il reste nettement
   au-dessus du hasard (39.9% à 8 joueurs) même s'il est en retrait par
   rapport au pic. La décomposition bombe/timeout (table 4) explique le
   mécanisme : à `bluff=0`, les parties se terminent presque toujours soit par
   les 4 DEFUSE trouvées (victoire Sherlock), soit par une bombe révélée tôt
   (`timeout` quasi nul, <3%). À `bluff=+3`, le taux de bombe révélée ET le
   taux de timeout grimpent tous les deux fortement (jusqu'à 75.7% / 16.0% à
   8 joueurs) : Sherlock fonce sur le Moriarty qui s'auto-désigne comme "gros
   porteur de DEFUSE", ce qui finit par lui faire révéler la bombe ou par
   épuiser les 4 manches sans compléter le plateau. À `bluff=-3`, ces deux
   taux augmentent aussi mais beaucoup plus modestement (56.4% / 3.7% à 8
   joueurs).

   **L'hypothèse "les Moriarty devraient sous-annoncer pour ralentir le jeu et
   gagner par timeout" est donc partiellement vraie** : sous-annoncer aide
   réellement Moriarty et augmente un peu le taux de timeout par rapport à
   `bluff=0`. Mais c'est en fait la **sur-annonce** qui reste l'arme la plus
   efficace pour Moriarty — par un mécanisme différent (rediriger les pinces
   de Sherlock vers une cible qui n'a pas vraiment les DEFUSE annoncés,
   provoquant à la fois plus de bombes révélées et plus de timeouts) plutôt
   que par occultation pure.

7. **`suspicion_weighted` n'apporte pas d'avantage net par rapport à
   `trust_weighted`, voire fait parfois moins bien.** L'idée — mélanger
   l'annonce et la taille de main restante d'un joueur déjà pris en flagrant
   délit — est parfois légèrement meilleure (ex. 5 joueurs, bluff=+3 : 14.6%
   contre 13.0% pour `trust_weighted`) mais parfois nettement pire (ex. 8
   joueurs, bluff=+1 : 23.8% contre 27.2%). Traquer un menteur démasqué est une
   arme à double tranchant : cela peut aussi bien exposer un DEFUSE caché que
   faire sortir la bombe de sa main.

**Verdict** : la mécanique pure de "qui pince où" est entièrement due au
hasard. Tout le "skill" de Time Bomb vient de la discussion/bluff à table
(déduire qui sont les Moriarty et où se trouvent les cartes), un aspect que
ce moteur ne capture qu'au travers des indices simulés. Le plafond
d'information parfaite est énorme (+85 points pour Sherlock, quasi 100% pour
Moriarty), mais tous les indices "réalistes" ne se valent pas : un indice
qui pointe vers l'objectif de Moriarty (où est la bombe) profite à Moriarty
même quand il est imparfait ou mensonger, alors qu'un indice qui pointe vers
l'objectif de Sherlock (qui a des DEFUSE) profite réellement à Sherlock —
mais seulement tant que les Moriarty restent honnêtes sur cet indice. La
discussion à table n'est donc bonne pour les "gentils" que si elle porte sur
*leurs* indices, pas sur ceux de Moriarty, et seulement si elle reste sincère
: dès que les Moriarty mentent sur leur compte de DEFUSE, l'avantage de
Sherlock s'érode — pas de façon symétrique. Un Moriarty qui sous-annonce pour
se cacher reste un adversaire qu'on peut encore traquer (Sherlock garde une
large avance sur le hasard) ; un Moriarty qui sur-annonce pour se faire
passer pour une cible juteuse aspire les pinces de Sherlock vers de mauvaises
cibles et ramène la partie presque au niveau du hasard pur.
