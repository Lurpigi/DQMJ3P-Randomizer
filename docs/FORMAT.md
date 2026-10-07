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

### 📁 RomFS sorgente

L'app non include file di gioco. Seleziona due cartelle già estratte: il RomFS del gioco base e quello dell'aggiornamento 1.3. Alla radice di entrambe deve esserci `data/`. L'app combina le cartelle in memoria e, se trova lo stesso percorso in entrambe, usa il file dell'update. Controlla le tabelle dei parametri, gli archivi degli incontri e i nomi dei modelli `.bch`, poi calcola un'impronta SHA-256. Legge i file senza modificarli. Non apre né estrae file `.3ds` o `.cia`.

### 🔧 Campi modificati

| Tabella | Struttura dei record | Campo specie |
|---|---|---|
| `MonsterParam.tp` / MONP | Header di 4 byte, record di 72 byte | Valore a 16 bit little-endian a +2; ID record a +0 |
| SMOT negli archivi ET / XBB | Header di 4 byte, record di 116 byte | Valore a 16 bit little-endian a +4; riferimenti MONP a +2, +6 e +8 |

Il randomizer modifica solo i campi specie indicati. Lunghezze, ID, riferimenti e tutti gli altri byte restano invariati, inclusi ENCT, MGRT e FADT. L'app non aggiunge record MONP e non riscrive posizioni o script.

### 🏅 Grado dei mostri

`KindParam.tp` / KINP contiene il codice del grado a +34. I codici da 1 a 8 corrispondono a F, E, D, C, B, A, S e SS. Il codice della famiglia si trova a +35.

### 📏 Taglia dei mostri

`KindParam.tp` / KINP contiene record da 120 byte. Il codice a 16 bit a +48 corrisponde agli slot in battaglia:

| Codice | Slot |
|---|---:|
| 0 o 1 | 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |

Gli altri codici sono sconosciuti. La mappatura corrisponde ai tratti Small, Normal, Mega, Giga e Ultra Body e alle [taglie del gioco](https://dragon-quest.jp/dqmj3/system/size.php). I codici 0 e 1 indicano entrambi la taglia S, ma rappresentano tipi di corpo diversi.

Un sostituto deve avere taglia nota, un record MONP e un modello presente nel gioco. Con entrambe le opzioni avanzate disattivate, i sostituti provengono dagli incontri selvatici e dai relativi riferimenti di battaglia.

### 🧩 Come si collegano i record

Il randomizer assegna i sostituti in base all'ID MONP, non alla specie. Ogni uso dello stesso ID riceve lo stesso sostituto. Record diversi della stessa specie possono riceverne di diversi. Il seed rende la mappatura riproducibile.

I filtri per famiglia e grado limitano il pool dei sostituti. Se li usi entrambi, ogni sostituto deve corrispondere a entrambi. I filtri non limitano i mostri originali da randomizzare. Se un record MONP è condiviso da più incontri, la modifica può riguardare ogni incontro che lo usa.

Il leader SMOT segue il riferimento MONP a +2 se entrambi i record indicano la stessa specie originale. Se i dati di partenza non coincidono, il leader riceve un sostituto separato della stessa taglia. L'app conserva questa differenza. I compagni restano collegati ai propri record MONP.

Nella copia RomFS usata per questa analisi, 596 ID MONP compaiono in più righe SMOT. Nei Prati Silenziosi, le definizioni Capporcello 4 e 14 condividono gli ID 10/11/12. La definizione 41 usa gli ID 97/98/99. Le definizioni 4 e 14 ricevono gli stessi sostituti perché condividono i record. Anche le entità che usano lo stesso record di battaglia restano uguali. Per distinguerle bisognerebbe modificare le assegnazioni degli spawn, che il randomizer non cambia.

### ⚠️ Eventi e boss

L'opzione dei sostituti speciali aggiunge specie compatibili di eventi e boss al catalogo. L'opzione non selvatici modifica anche record MONP fuori dagli incontri selvatici. Può riguardare più dei soli boss.

`MonsterPartyTable.tp` / PTYT contiene valori numerici che coincidono con ID MONP. Il manifest segnala queste corrispondenze, ma il loro significato non è confermato. Gli script delle scene possono mantenere modelli fissi. I controlli dei file non dimostrano che animazioni, reclutamento o progressione funzionino in gioco.
