# File formats and limits / Formati e limiti

[English](#english) · [Italiano](#italiano)

## English

### 📁 Source RomFS

The app does not include game files. Select two already extracted folders: the base game's RomFS and update 1.3's RomFS. Each root must contain `data/`. The app combines the folders in memory, using update files when both folders contain the same path. It checks the required parameter tables, encounter archives, and `.bch` model filenames, then calculates a SHA-256 fingerprint. It reads the source without changing it. It does not open or extract `.3ds` or `.cia` files.

### 🔧 Fields that change

| Table | Record layout | Species field |
|---|---|---|
| `MonsterParam.tp` / MONP | 4-byte header, 72-byte records | 16-bit little-endian value at +2; record ID at +0 |
| SMOT in ET / XBB archives | 4-byte header, 116-byte records | 16-bit little-endian value at +4; MONP references at +2, +6, and +8 |

The randomizer changes only the species fields above. File lengths, IDs, references, and all other bytes stay the same. This includes ENCT, MGRT, and FADT. The app does not add MONP records or rewrite positions and scripts.

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

A replacement must have a known size, a MONP record, and an in-game model. With both advanced options off, replacements come from wild encounters and their battle references.

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

Il randomizer modifica solo i campi della specie indicati. Non cambia la lunghezza dei file, gli ID, i riferimenti o gli altri byte. I dati ENCT, MGRT e FADT restano invariati. L'app non aggiunge record MONP e non riscrive posizioni o script.

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

Un sostituto deve avere una taglia nota, un record MONP e un modello presente nel gioco. Se entrambe le opzioni avanzate sono disattivate, i sostituti vengono scelti tra i mostri degli incontri selvatici e i relativi riferimenti di battaglia.

### 🧩 Collegamento tra i record

Il randomizer assegna i sostituti in base all'ID MONP, non alla specie. Tutti gli incontri che usano lo stesso ID ricevono lo stesso sostituto. Record diversi della stessa specie possono invece ricevere sostituti diversi. Il seed permette di ottenere la stessa mappatura a ogni esecuzione.

I filtri per famiglia e grado restringono i possibili sostituti. Se li usi entrambi, ogni sostituto deve rispettarli entrambi. I filtri non limitano i mostri originali da sostituire. Se più incontri condividono un record MONP, la modifica riguarda tutti quegli incontri.

Per il mostro leader, il randomizer usa il riferimento MONP all'offset +2 se il record SMOT e il record MONP indicano la stessa specie di partenza. Se i dati di partenza non coincidono, il leader riceve un sostituto distinto della stessa taglia. L'app mantiene questa differenza. Gli alleati restano associati ai rispettivi record MONP.

Nel RomFS analizzato, 596 ID MONP compaiono in più righe SMOT. Nei Prati Silenziosi, le definizioni 4 e 14 di Capporcello condividono gli ID 10/11/12; la definizione 41 usa gli ID 97/98/99. Le definizioni 4 e 14 ricevono gli stessi sostituti perché condividono i record. Anche gli incontri che usano lo stesso record di battaglia ricevono lo stesso sostituto. Per assegnare sostituti diversi bisognerebbe modificare i punti di comparsa, cosa che il randomizer non fa.

### ⚠️ Eventi e boss

L'opzione per includere mostri degli eventi e dei boss aggiunge ai possibili sostituti le specie con taglia e modello compatibili. L'opzione per gli incontri non selvatici modifica anche i record MONP usati fuori dagli incontri selvatici. Può riguardare eventi, boss, personaggi e tornei.

`MonsterPartyTable.tp` / PTYT contiene valori numerici che corrispondono a ID MONP. Il manifest elenca queste corrispondenze, ma il loro significato non è stato confermato. Gli script delle scene possono mantenere i modelli originali. Le verifiche dei file non garantiscono che animazioni, reclutamento o avanzamento della storia funzionino correttamente nel gioco.
