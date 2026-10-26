# File formats and limits / Formati e limiti / Formats et limites

[English](#english) · [Italiano](#italiano) · [Français](#français)

## English

### 📁 Source RomFS

The app does not include game files. Select two already extracted folders: the base game's RomFS and update 1.3's RomFS. Each root must contain `data/`. The app combines the folders in memory, using update files when both folders contain the same path. It checks the required parameter tables, encounter archives, and `.bch` model filenames, then calculates a SHA-256 fingerprint. It reads the source without changing it. It does not open or extract `.3ds` or `.cia` files.

### 🔧 Fields that change

| Table | Record layout | Species field |
|---|---|---|
| `MonsterParam.tp` / MONP | 4-byte header, 72-byte records | 16-bit little-endian value at +2; record ID at +0 |
| SMOT in ET / XBB archives | 4-byte header, 116-byte records | 16-bit little-endian value at +4; MONP references at +2, +6, and +8 |

The randomizer changes the species fields above, the MONP skill fields at +64/+66/+68 and, when enabled, the MONP level field at +24. File lengths, IDs, references, and all other bytes stay the same. This includes ENCT, MGRT, and FADT. The app does not add MONP records or rewrite positions and scripts.

### 🏅 Monster rank

`KindParam.tp` / KINP stores the rank code at +34. Codes 1–8 map to F, E, D, C, B, A, S, and SS. The family code follows at +35.

### 📏 Monster size

`KindParam.tp` / KINP has 120-byte records. The 16-bit code at +48 maps to battle slots:

| Code | Slots |
|---|---:|
| 0 or 1 | 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |

Other codes are unknown. The mapping matches the Small, Normal, Mega, Giga, and Ultra Body traits and the [game's size categories](https://dragon-quest.jp/dqmj3/system/size.php). Codes 0 and 1 both mean size S, but represent different body types.

A replacement must have a known size, a MONP record, and an in-game model. With all advanced options off, replacements come from wild encounters and their battle references.

### 🎚️ Monster level

`MonsterParam.tp` / MONP stores the starting level as a 16-bit little-endian value at +24. When enabled, the level option assigns each selected MONP record a seeded level from 1 to 99. Encounters that share a MONP ID also share its level.

### ✨ Skill sets

`KindParam.tp` / KINP stores each species' native skill set ID as a 16-bit little-endian value at +66. MONP stores three skill set IDs at +64, +66 and +68. By default, the first MONP slot receives the replacement species' native set. The other two slots are retained, with duplicate sets cleared. A species with no native set has a zero in its first slot.

`--randomize-skills` assigns random sets to the first slot and any occupied supplemental slots. The pool contains nonzero skill IDs already assigned in KINP or nonempty MONP records; family and rank filters do not restrict it. Sets cannot repeat within one record. Empty supplemental slots stay empty; if the pool is too small, remaining slots are cleared. Choices use the seed and MONP ID, so shared records keep the same sets. The manifest, config and spoiler record the selected mode and assignments.

### 🧩 How records map

The randomizer assigns replacements by MONP record ID, not by species. Every use of an ID gets the same replacement. Different records for one species can get different replacements. The seed keeps the mapping reproducible.

The family and rank filters limit the replacement pool. When both are set, a replacement must match both. They do not limit the original monsters being randomized. If a MONP record is shared by different encounters, changing that record can affect each encounter that uses it.

An SMOT leader follows the MONP reference at +2 when both records name the same original species. If they do not match in the source data, the leader gets a separate replacement of the same size. The app keeps that original mismatch. Allies stay linked to their MONP records.

In the RomFS snapshot used for this analysis, 596 MONP IDs appear in multiple SMOT rows. In Prati Silenziosi, Capporcello definitions 4 and 14 share IDs 10/11/12. Definition 41 uses IDs 97/98/99. Definitions 4 and 14 get the same replacements because they share records. Physical entities that use the same battle record also stay the same. Separating them would require changing spawn assignments, which this randomizer does not edit.

### ⚠️ Events and bosses

The special-donor option adds compatible event and boss species to the replacement pool. The non-wild option also changes MONP records outside wild encounters. It can affect more than bosses.

`MonsterPartyTable.tp` / PTYT contains numeric values that match MONP IDs. The manifest reports these overlaps, but their meaning is not confirmed. Scene scripts can keep fixed models. File checks cannot prove that animations, recruitment, or story progress work in game.

## Italiano

### 📁 Cartelle RomFS

L'app non include file di gioco. Seleziona le cartelle RomFS già estratte del gioco base e dell'aggiornamento 1.3. Alla radice di entrambe deve esserci `data/`. L'app le combina in memoria e, se lo stesso percorso è presente in entrambe, usa il file dell'aggiornamento. Controlla le tabelle dei parametri, gli archivi degli incontri e i nomi dei modelli `.bch`, poi calcola un'impronta SHA-256. Legge i file senza modificarli. Non apre né estrae file `.3ds` o `.cia`.

### 🔧 Campi modificati

| Tabella | Struttura dei record | Campo della specie |
|---|---|---|
| `MonsterParam.tp` / MONP | Intestazione di 4 byte, record di 72 byte | Valore little-endian a 16 bit all'offset +2; ID del record all'offset +0 |
| SMOT negli archivi ET / XBB | Intestazione di 4 byte, record di 116 byte | Valore little-endian a 16 bit all'offset +4; riferimenti MONP agli offset +2, +6 e +8 |

Il randomizer modifica i campi della specie indicati, le abilità MONP agli offset +64/+66/+68 e, se attivi l'opzione, il livello MONP all'offset +24. Non cambia la lunghezza dei file, gli ID, i riferimenti o gli altri byte. I dati ENCT, MGRT e FADT restano invariati. L'app non aggiunge record MONP e non riscrive posizioni o script.

### 🏅 Grado dei mostri

`KindParam.tp` / KINP memorizza il codice del grado all'offset +34. I codici da 1 a 8 corrispondono a F, E, D, C, B, A, S e SS. Il codice della famiglia si trova all'offset +35.

### 📏 Taglia dei mostri

`KindParam.tp` / KINP è organizzata in record da 120 byte. Il codice a 16 bit all'offset +48 indica il numero di slot in battaglia:

| Codice | Slot |
|---|---:|
| 0 o 1 | 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |

Gli altri codici non sono riconosciuti. La mappatura corrisponde ai tratti Small, Normal, Mega, Giga e Ultra Body e alle [taglie del gioco](https://dragon-quest.jp/dqmj3/system/size.php). I codici 0 e 1 indicano entrambi la taglia S, ma rappresentano tipi di corpo diversi.

Un sostituto deve avere una taglia nota, un record MONP e un modello presente nel gioco. Se tutte le opzioni avanzate sono disattivate, i sostituti vengono scelti tra i mostri degli incontri selvatici e i relativi riferimenti di battaglia.

### 🎚️ Livello dei mostri

`MonsterParam.tp` / MONP memorizza il livello iniziale in un valore little-endian a 16 bit all'offset +24. Se attivi l'opzione, ogni record MONP selezionato riceve un livello deterministico da 1 a 99. Gli incontri che condividono un ID MONP condividono anche il livello.

### ✨ Set di abilità

`KindParam.tp` / KINP memorizza l'ID del set nativo di ciascuna specie in un valore little-endian a 16 bit all'offset +66. MONP memorizza tre ID di set agli offset +64, +66 e +68. Di norma, il primo slot MONP riceve il set nativo della nuova specie. Gli altri due vengono conservati, eliminando eventuali duplicati. Se una specie non ha un set nativo, il primo slot vale zero.

`--randomize-skills` assegna set casuali al primo slot e agli slot aggiuntivi occupati. Il pool contiene gli ID non nulli già assegnati in KINP o nei record MONP con una specie; i filtri per famiglia e grado non lo restringono. Un record non può ricevere set duplicati. Gli slot aggiuntivi vuoti restano vuoti; se i set disponibili non bastano, gli slot rimanenti vengono azzerati. Le scelte dipendono dal seed e dall'ID MONP, quindi i record condivisi ricevono gli stessi set. Manifest, configurazione e riepilogo riportano la modalità scelta e le assegnazioni.

### 🧩 Collegamento tra i record

Il randomizer assegna i sostituti in base all'ID MONP, non alla specie. Tutti gli incontri che usano lo stesso ID ricevono lo stesso sostituto. Record diversi della stessa specie possono invece ricevere sostituti diversi. Il seed permette di ottenere la stessa mappatura a ogni esecuzione.

I filtri per famiglia e grado restringono i possibili sostituti. Se li usi entrambi, ogni sostituto deve rispettarli entrambi. I filtri non limitano i mostri originali da sostituire. Se più incontri condividono un record MONP, la modifica riguarda tutti quegli incontri.

Per il mostro leader, il randomizer usa il riferimento MONP all'offset +2 se il record SMOT e il record MONP indicano la stessa specie di partenza. Se i dati di partenza non coincidono, il leader riceve un sostituto distinto della stessa taglia. L'app mantiene questa differenza. Gli alleati restano associati ai rispettivi record MONP.

Nel RomFS analizzato, 596 ID MONP compaiono in più righe SMOT. Nei Prati Silenziosi, le definizioni 4 e 14 di Capporcello condividono gli ID 10/11/12; la definizione 41 usa gli ID 97/98/99. Le definizioni 4 e 14 ricevono gli stessi sostituti perché condividono i record. Anche gli incontri che usano lo stesso record di battaglia ricevono lo stesso sostituto. Per assegnare sostituti diversi bisognerebbe modificare i punti di comparsa, cosa che il randomizer non fa.

### ⚠️ Eventi e boss

L'opzione per includere mostri degli eventi e dei boss aggiunge ai possibili sostituti le specie con taglia e modello compatibili. L'opzione per gli incontri non selvatici modifica anche i record MONP usati fuori dagli incontri selvatici. Può riguardare eventi, boss, personaggi e tornei.

`MonsterPartyTable.tp` / PTYT contiene valori numerici che corrispondono a ID MONP. Il manifest elenca queste corrispondenze, ma il loro significato non è stato confermato. Gli script delle scene possono mantenere i modelli originali. Le verifiche dei file non garantiscono che animazioni, reclutamento o avanzamento della storia funzionino correttamente nel gioco.

## Français

### 📁 Source RomFS

L'application ne contient paqs de fichiers du jeu. Sélectionnez des dossiers déjà extraits: Les RomFS du jeu de base et de la mise à jour 1.3. Chaque racine doit contenir `data/`. L'application combine les dossiers en mémoire, Utilisant les fichiers de la mise à jour quand les fichiers ont la même arborescence. Elle vérifie les paramètres de tableau requis, archives de rencontres et les noms des fichiers de modèles`.bch`, puis calcule la trace SHA-256. La source est lue sans être changée. L'application ne lit ou n'extrait ni les fichiers `.3ds`, ni les fichiers `.cia`.

### 🔧 Champs qui changent

| Tableau | Structure des entrées | Champ des espèces |
|---|---|---|
| `MonsterParam.tp` / MONP | header de 4 bytes, entrées de 72 bytes | valeur de 16 bits petit-boutisme à +2; entrée de l'ID à +0 |
| SMOT en ET / archives XBB | header de 4 bytes, entrées de 116 bytes | valeur de 16 bits petit-boutisme à +4; Références MONP à +2, +6 et +8 |

Le randomizer modifie les champs d'espèce ci-dessus, les compétences MONP à +64/+66/+68 et, si l'option est activée, le niveau MONP à +24. La longueur des fichiers, les IDs, les références et tous les autres octets restent inchangés. Cela inclut ENCT, MGRT et FADT. L'application n'ajoute pas d'entrées MONP et ne réécrit ni les positions ni les scripts.

### 🏅 Rang de monstre

`KindParam.tp` / KINP stoque le code de rang à +34. les codes 1–8 relient à F, E, D, C, B, A, S, et SS. Le code de famille suikt à +35.

### 📏 Taille des monstres

`KindParam.tp` / KINP a des entrées de 120 bytes. Le code de 16 bits à +48 lie aux cases en combat:

| Code | Cases |
|---|---:|
| 0 ou 1 | 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |

Les autrs codes sont inconnus. Les liaisons sont conformes aux attributs Petit corps, Corps normal, Mega corps, Giga corps et Ultra corps, et aux [Catégories de taille du jeu](https://dragon-quest.jp/dqmj3/system/size.php). Les codes 0 et 1 représentent tous deux des monstres de 1 case, mais représentnent des types de corps différents.

Un remplacement doit avoir une taille connue, une entrée MONP et un modèle en jeu. Avec toutes les options avancées désactivées, les remplacements viennent des rencontres sauvages et de leurs références de combat.

### 🎚️ Niveau des monstres

`MonsterParam.tp` / MONP stocke le niveau initial comme valeur little-endian de 16 bits à +24. Si l'option est activée, chaque entrée MONP sélectionnée reçoit un niveau déterminé par la graine, entre 1 et 99. Les rencontres qui partagent un ID MONP partagent aussi son niveau.

### ✨ Sets de compétences

`KindParam.tp` / KINP stocke l'ID du set natif de chaque espèce dans une valeur little-endian de 16 bits à +66. MONP stocke trois IDs de sets à +64, +66 et +68. Par défaut, le premier emplacement MONP reçoit le set natif de la nouvelle espèce. Les deux autres sont conservés, sans doublons. Une espèce sans set natif a un zéro dans le premier emplacement.

`--randomize-skills` attribue des sets aléatoires au premier emplacement et aux emplacements supplémentaires occupés. Le pool contient les IDs non nuls déjà attribués dans KINP ou dans les entrées MONP avec une espèce ; les filtres de famille et de rang ne le limitent pas. Aucun set ne peut apparaître deux fois dans une entrée. Les emplacements supplémentaires vides restent vides ; si le pool est trop petit, les emplacements restants sont vidés. La graine et l'ID MONP déterminent les choix, donc les entrées partagées gardent les mêmes sets. Le manifeste, la configuration et le fichier de spoilers indiquent le mode et les attributions.

### 🧩 Comment les entrées sont liées

Le randomizer assigne les remplacements par ID d'entrée MONP, pas par espèce. Chaque utilisation d'un ID reçoit le même remplacement. DDes entrées différentes pour une espèce peuvent avir des remplacements différents. La graine rend les liaisons reproductibles.

Les filtres de rang et de famille limitent les possibilités de monstres remplaçants. Quand les deux sont effectifs, un remplacement doit correspondre aux deux filtres. Mais ils ne limitent pas les monstres qui sont randomizés. Si une entrée MONP est partagée par des rencontres différentes, alors changer cette entrée va affecter toutes les rencontres qui l'utilisent.

Un chef SMOT suit la référence MONP à +2 quand les deux entrées indiquent la même espèce. Si ils ne correspondent pas dans les données source, le chef reçoit un remplacement différent de la même taille. L'application conserve ce décalage originel. Les alliés restent liés à leurs entrées MONP.

Dans la version du RomFS utilisé pour cette analyse, 596 IDs MONP apparaissent dans plusieurs lignes SMOT. Dans les Plaines Silencieuses, les définitions des Chaporcs magiques 4 et 14 partagent les ID 10/11/12. La définition 41 utilise les ID 97/98/99. Les définitions 4 et 14 ont les mêmes remplacements car elles partagent des entrées. Les entités physiques qui utilisent la même entrée de combat restent aussi les mêmes. Les séparer nécessiterait de changer les règles d'apparition, ce que ce randomizer ne change pas.

### ⚠️ Évènements et Boss

Le paramètre qui rajoute les boss et monstres d'évènement ajoute les entrées correspondantes et compatibles aux remplacements possibles. Le paramètre d'inclure les monstres hors combats change aussi les entrées MONP en dehors des rencontres de monstres non-sauvages. Plus que les boss peubvent être affectés.

`MonsterPartyTable.tp` / PTYT contient des valeurs numériques qui correspondent aux ID MONP. Le manifeste indique ces superpositions, mais leur signification n'est pas confirmée. Les scripts de scènes peuvent garder des modèles fixes. Les vérifications de fichiers ne peuvent pas prouver le fonctionnement les animations, dressages ou de la progression dans le jeu.
