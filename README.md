# DQMJ3P Randomizer
[English](#english) · [Italiano](#italiano) · [Français](#français)


<a href="https://github.com/Lurpigi/DQMJ3P-Randomizer/releases/latest">
  <img src="https://img.shields.io/github/v/release/Lurpigi/DQMJ3P-Randomizer?display_name=tag" alt="Latest release / Ultima release">
</a>

<p align="center">
  <img src="https://raw.githubusercontent.com/Lurpigi/DQMJ3P-Randomizer/main/img/img.png" alt="DQMJ3P Randomizer icon / Icona del DQMJ3P Randomizer" width="220">
</p>



## English

A small randomizer for *Dragon Quest Monsters: Joker 3 Professional*. Pick a seed to replace encounter monsters while keeping their size. Use the same seed and options to get the same results again.

For the English fan patch, see [DQMJ3P English Fixed](https://github.com/Akoi89/DQMJ3P-english-fixed).

### Get the RomFS folders

Use one of these methods to extract the base game RomFS and update 1.3 RomFS.

#### Method 1: HackingToolkit3DS

You need a `.cia` or `.3ds` file for the base game and another for update 1.3.

1. Download [HackingToolkit3DS v9](https://github.com/Asia81/HackingToolkit9DS/releases/tag/9) and extract its archive.
2. Put the base game file in the HackingToolkit folder and start the extraction option for its format (`.cia` or `.3ds`). When asked whether to decompress `code.bin`, choose **No**.
3. Rename or move the resulting `ExtractedRomFS` folder to `romfs-base`.
4. Repeat steps 2 and 3 for update 1.3. Rename or move its `ExtractedRomFS` folder to `romfs-update`.

#### Method 2: Azahar

The base game and update 1.3 must be installed in Azahar.

1. Open Azahar and right-click **DQMJOKER3 PRO**.
2. Choose **Extract RomFS**. Azahar extracts the RomFS folders and opens their locations.
3. Rename the base game folder `00040000001ACB00` to `romfs-base` and the update folder `0004000E001ACB00` to `romfs-update`. Move them wherever you like.

#### Method 3: GodMode9

The base game and update 1.3 must be installed on a 3DS with Luma3DS and GodMode9.

The menu labels below are in English. They may appear translated, depending on your GodMode9 language.

1. Start GodMode9. On most setups, hold **START** while turning on the 3DS.
2. Press **HOME**, then choose **Title manager** and **[A:] SD**.
3. Select `00040000001ACB00 DQMJOKER3 PRO (CTR-U-BDQJ) (J) (v0.0.0)` and choose **Open title folder**.
4. Select the `.tmd` file, choose **TMD file options...** > **Mount CXI/NDS to drive**, then press **A**.
5. Highlight the `romfs` folder without opening it. Press **R** + **A**, then choose **Copy to 0:/gm9/out**.
6. Open **[0:] SD** > `/gm9/out`. Highlight `romfs`, press **R** + **X**, and rename it to `romfs-base`.
7. Repeat steps 2–6 for `0004000E001ACB00 DQMJOKER3 PRO (CTR-U-BDQJ) (J) (v3.0.0)`. Name the folder `romfs-update`.
8. Press **START** to restart the 3DS, or **START** + **R** to turn it off. Copy both folders from the SD card to your computer.

Whichever method you use, check that both folders contain `data/` at the top level:

   ```text
   romfs-base/data/
   romfs-update/data/
   ```

In the app, select `romfs-base` and `romfs-update`, not their `data/` subfolders.

### 🚀 Start

You need Python 3.10 or later with Tkinter. From the program folder, run:

```powershell
python randomizer_app.py
```

Choose **EN**, **IT** or **FR** in the top-right corner to switch the app language.

The app does not include game files and does not open CIA or 3DS files. It needs the already extracted RomFS folders for the base game and update 1.3. The app combines them while it runs, with update files taking precedence. Keep the app folder together when you move it.

### 🎲 Make a package

1. Select the base game RomFS folder and the update 1.3 RomFS folder. If you still need to extract them, follow [Get the RomFS folders](#get-the-romfs-folders).
2. Choose the families allowed for replacements. This filter limits the replacement pool; it does not change which original monsters are randomized.
3. Choose the allowed ranks. If you use both filters, a replacement must match both.
4. Enter a seed. Use `0` to get a random one.
5. Open **Advanced options** if needed. Hover over **ⓘ** for details.
6. Optional: select **Randomize levels too (1–99)**.
7. Optional: select **Use random skill sets**.
8. Optional: select **Use event and boss species as replacements**.
9. Optional: select **Also change records outside wild encounters (experimental)**.
10. Click **Create package**. Find the folder and ZIP in `output/`.

The same seed and options always assign the same replacement to each battle record. Encounters of the same species can differ if they use different records. Encounters that share a record keep the same replacement.

When level randomization is enabled, the seed also assigns each selected monster record a level from 1 to 99. Records shared by multiple encounters get the same level.

By default, each replacement receives its new species' native skill set. Supplemental sets are kept, with duplicates removed. **Use random skill sets** assigns random sets to occupied slots instead, using sets already present in the game data. The same seed gives the same result, and a monster cannot receive duplicate sets.

The package contains the modified files, a manifest, a spoiler file, a configuration file, and this README with installation steps. The app checks both selected folders before creating it. Source game files are not included in the app download.

### Install the mod

**3DS with Luma3DS**

1. Turn off the 3DS. Hold **SELECT** while turning it on, enable **Enable game patching**, then press **START** to save.
2. On the SD card, create `/luma/titles/00040000001ACB00/romfs/`.
3. Copy the randomizer ZIP's `romfs/` contents into this folder. Replace matching files.
4. Put the SD card back in the 3DS and start the game.

**Azahar on PC or Android**

Install the game and update 1.3 in Azahar first.

PC:

1. In Azahar's game list, right-click the game and choose **Open Mods Location**.
2. Create a `romfs/` folder in the mod folder if it does not exist.
3. Copy the randomizer ZIP's `romfs/` contents into it. Replace matching files.

Android:

1. Open Azahar's data folder with a file manager.
2. Create `load/mods/00040000001ACB00/romfs/`.
3. Copy the randomizer ZIP's `romfs/` contents into that folder.

### Check or remove the mod

Start the game and revisit an area to refresh its encounters. To remove the randomizer, delete the files listed in the package manifest.


### ⌨️ Use the command line

```powershell
python randomize.py --base-romfs "C:\path\to\base-romfs" --update-romfs "C:\path\to\update-romfs" --seed 42
python randomize.py --base-romfs "C:\path\to\base-romfs" --update-romfs "C:\path\to\update-romfs" --seed 42 --randomize-skills
python randomize.py --base-romfs "C:\path\to\base-romfs" --update-romfs "C:\path\to\update-romfs" --seed 42 --include-special-donors --include-nonwild-instances --randomize-levels
python randomize.py --base-romfs "C:\path\to\base-romfs" --update-romfs "C:\path\to\update-romfs" --seed 42 --family slime --family material
python randomize.py --base-romfs "C:\path\to\base-romfs" --update-romfs "C:\path\to\update-romfs" --seed 42 --family slime --rank f --rank ss
```

The randomizer assigns replacements by battle record. Run `python randomize.py --help` to see all options. For installation, see [Install the mod](#install-the-mod). For technical details, see [FORMAT.md](https://github.com/Lurpigi/DQMJ3P-Randomizer/blob/main/docs/FORMAT.md#english).

### 📚 Guides

- [File formats and technical details](https://github.com/Lurpigi/DQMJ3P-Randomizer/blob/main/docs/FORMAT.md#english)

### 💬 Community

Join the [DQMJ3P Discord server](https://discord.com/invite/W5yRJpDd5e).

<p align="center" style="margin-top:3rem">
  <img src="https://raw.githubusercontent.com/Lurpigi/DQMJ3P-Randomizer/main/img/app.png" alt="DQMJ3P Randomizer app / Interfaccia del DQMJ3P Randomizer" width="700">
</p>

## Italiano

Un semplice randomizer per *Dragon Quest Monsters: Joker 3 Professional*. Scegli un seed per cambiare i mostri che incontri senza modificarne la taglia. Con lo stesso seed e le stesse opzioni ottieni sempre gli stessi risultati.

### Estrai le cartelle RomFS

Scegli uno dei metodi seguenti per estrarre il RomFS del gioco base e quello dell'aggiornamento 1.3.

#### Metodo 1: HackingToolkit3DS

Ti servono un file `.cia` o `.3ds` del gioco base e uno dell'aggiornamento 1.3.

1. Scarica [HackingToolkit3DS v9](https://github.com/Asia81/HackingToolkit9DS/releases/tag/9) e decomprimi l'archivio.
2. Copia il file del gioco base nella cartella di HackingToolkit e avvia l'estrazione per il suo formato (`.cia` o `.3ds`). Se ti chiede di decomprimere `code.bin`, scegli **No**.
3. Rinomina la cartella `ExtractedRomFS` in `romfs-base`.
4. Estrai l'aggiornamento 1.3 allo stesso modo e rinomina la cartella `ExtractedRomFS` ottenuta in `romfs-update`.

#### Metodo 2: Azahar

Il gioco base e l'aggiornamento 1.3 devono essere installati in Azahar.

1. Apri Azahar e fai clic con il tasto destro su **DQMJOKER3 PRO**.
2. Scegli **Extract RomFS**. Azahar estrae le cartelle RomFS e apre le rispettive posizioni.
3. Rinomina la cartella del gioco base `00040000001ACB00` in `romfs-base` e quella dell'aggiornamento `0004000E001ACB00` in `romfs-update`. Puoi spostarle dove preferisci.

#### Metodo 3: GodMode9

Il gioco base e l'aggiornamento 1.3 devono essere installati su un 3DS con Luma3DS e GodMode9.

Le voci dei menu qui sotto sono in inglese; possono apparire tradotte in base alla lingua di GodMode9.

1. Avvia GodMode9. Nella maggior parte delle configurazioni, tieni premuto **START** mentre accendi il 3DS.
2. Premi **HOME**, poi scegli **Title manager** e **[A:] SD**.
3. Seleziona `00040000001ACB00 DQMJOKER3 PRO (CTR-U-BDQJ) (J) (v0.0.0)` e scegli **Open title folder**.
4. Seleziona il file `.tmd`, scegli **TMD file options...** > **Mount CXI/NDS to drive**, poi premi **A**.
5. Evidenzia la cartella `romfs` senza aprirla. Premi **R** + **A**, poi scegli **Copy to 0:/gm9/out**.
6. Apri **[0:] SD** > `/gm9/out`. Evidenzia `romfs`, premi **R** + **X**, poi rinominala `romfs-base`.
7. Ripeti i passaggi 2–6 per `0004000E001ACB00 DQMJOKER3 PRO (CTR-U-BDQJ) (J) (v3.0.0)`. Rinomina la cartella in `romfs-update`.
8. Premi **START** per riavviare il 3DS o **START** + **R** per spegnerlo. Copia entrambe le cartelle dalla scheda SD al computer.

Qualunque metodo tu scelga, controlla che `data/` si trovi al livello principale di entrambe le cartelle:

   ```text
   romfs-base/data/
   romfs-update/data/
   ```

Nell'app, seleziona `romfs-base` e `romfs-update`, non le sottocartelle `data/`.

### 🚀 Avvio

Serve Python 3.10 o una versione successiva con Tkinter. Dalla cartella del programma, esegui:

```powershell
python randomizer_app.py
```

Scegli **EN**, **IT** o **FR** in alto a destra per cambiare la lingua dell'app.

Il programma non include file di gioco né apre file CIA o 3DS. Per funzionare, richiede le cartelle RomFS già estratte del gioco base e dell'aggiornamento 1.3. Le carica in memoria e usa i file dell'aggiornamento quando lo stesso percorso è presente in entrambe. Se sposti il programma, sposta tutta la sua cartella.

### 🎲 Crea un pacchetto

1. Seleziona la cartella RomFS del gioco base e quella dell'aggiornamento 1.3. Se devi ancora estrarle, segui [Estrai le cartelle RomFS](#estrai-le-cartelle-romfs).
2. Scegli le famiglie ammesse per i sostituti. Il filtro decide quali mostri possono diventare sostituti, non quali incontri vengono randomizzati.
3. Scegli i gradi ammessi. Se usi entrambi i filtri, ogni sostituto deve rispettarli entrambi.
4. Inserisci un seed. Usa `0` per generarne uno casuale.
5. Apri **Opzioni avanzate** se ti servono. Per i dettagli, passa il puntatore su **ⓘ**.
6. Facoltativo: seleziona **Randomizza anche il livello (1–99)**.
7. Facoltativo: seleziona **Usa set di abilità casuali**.
8. Facoltativo: seleziona **Usa anche mostri degli eventi e dei boss come sostituti**.
9. Facoltativo: seleziona **Modifica anche i record fuori dagli incontri selvatici (sperimentale)**.
10. Premi **Crea pacchetto**. Trovi i file in `output/`.

Con lo stesso seed e le stesse opzioni, ogni record di battaglia riceve sempre lo stesso sostituto. Incontri della stessa specie possono ricevere sostituti diversi se usano record diversi. Se più incontri condividono un record, ricevono lo stesso sostituto.

Se attivi la randomizzazione dei livelli, il seed assegna a ogni record MONP selezionato un livello da 1 a 99. I record condivisi da più incontri ricevono lo stesso livello.

Di norma, ogni sostituto riceve il set di abilità nativo della nuova specie. I set aggiuntivi vengono conservati, eliminando eventuali duplicati. **Usa set di abilità casuali** assegna invece set casuali agli slot occupati, scegliendoli tra quelli già presenti nei dati di gioco. Lo stesso seed dà lo stesso risultato e un mostro non può ricevere set duplicati.

Il pacchetto include i file modificati, un manifest, il riepilogo delle sostituzioni, un file di configurazione e questo README con le istruzioni per l'installazione. Prima di crearlo, l'app controlla entrambe le cartelle selezionate. Il download del programma non include file di gioco.

### Installa la mod

**3DS con Luma3DS**

1. Spegni il 3DS. Tieni premuto **SELECT** mentre lo accendi, attiva **Enable game patching** e premi **START** per salvare le impostazioni.
2. Sulla scheda SD, crea `/luma/titles/00040000001ACB00/romfs/`.
3. Copia in questa cartella i file contenuti in `romfs/` nello ZIP del randomizer. Sostituisci i file con lo stesso nome.
4. Reinserisci la scheda SD nel 3DS e avvia il gioco.

**Azahar su PC o Android**

In Azahar, installa il gioco e l'aggiornamento 1.3.

**PC**

1. Nell'elenco dei giochi di Azahar, fai clic con il tasto destro sul gioco e scegli **Open Mods Location**.
2. Se non esiste, crea la cartella `romfs/` nella cartella della mod.
3. Copia lì i file contenuti in `romfs/` nello ZIP del randomizer. Sostituisci i file con lo stesso nome.

**Android**

1. Apri la cartella dei dati di Azahar con un gestore file.
2. Crea `load/mods/00040000001ACB00/romfs/`.
3. Copia in questa cartella i file contenuti in `romfs/` nello ZIP del randomizer.

### Controlla o rimuovi la mod

Avvia il gioco ed entra in una nuova area per caricare gli incontri modificati. Per rimuovere la mod, elimina i file elencati nel manifest del pacchetto.


### ⌨️ Usa la riga di comando

```powershell
python randomize.py --base-romfs "C:\percorso\romfs-base" --update-romfs "C:\percorso\romfs-update" --seed 42
python randomize.py --base-romfs "C:\percorso\romfs-base" --update-romfs "C:\percorso\romfs-update" --seed 42 --randomize-skills
python randomize.py --base-romfs "C:\percorso\romfs-base" --update-romfs "C:\percorso\romfs-update" --seed 42 --include-special-donors --include-nonwild-instances --randomize-levels
python randomize.py --base-romfs "C:\percorso\romfs-base" --update-romfs "C:\percorso\romfs-update" --seed 42 --family slime --family material
python randomize.py --base-romfs "C:\percorso\romfs-base" --update-romfs "C:\percorso\romfs-update" --seed 42 --family slime --rank f --rank ss
```

Il randomizer assegna i sostituti in base al record di battaglia. Esegui `python randomize.py --help` per vedere tutte le opzioni. Per installare la mod, consulta [Installa la mod](#installa-la-mod). Per i dettagli tecnici, consulta [FORMAT.md](https://github.com/Lurpigi/DQMJ3P-Randomizer/blob/main/docs/FORMAT.md#italiano).

### 📚 Guide

- [Formati e dettagli tecnici](https://github.com/Lurpigi/DQMJ3P-Randomizer/blob/main/docs/FORMAT.md#italiano)

### 💬 Comunità

Entra nel [server Discord di DQMJ3P](https://discord.com/invite/W5yRJpDd5e).

## Français

Un petit randomizer pour *Dragon Quest Monsters: Joker 3 Professional*. Choisissez une Seed pour remplacer les monstres rencontrés (en gardant la même taille). Utilisez la même Seed et les mêmes paramuètres pour avoir les mêmes résultats.

Pour la traduction française non-officielle, allez voir [Le topic correspondant sur Dragon Quest Fan](https://dragonquest-fan.com/forum/index.php?subjectID=14911).

Cette application ne contient pas de ROMs comme des fichiers .3ds ou .cia. Veuillez vous procurer les vôtres vous-même.

### Récupérer le dossier RomFS

#### Méthode 1 - Via HackingToolkit3DS
> Pour cette méthode, vous aurez besoin de fichiers `.cia` ou `.3ds` pour les jeu de base et mise à jour 1.3.

1. Téléchargez [HackingToolkit3DS v9](https://github.com/Asia81/HackingToolkit9DS/releases/tag/9) et allez extraire l'archive quelque part.
2. Mettez les fichiers .3ds/.cia dans le dossier de HackingToolkit3DS folder
3. Lancez l'extraction du jeu de base pour le format correspondant (`.cia` ou `.3ds`). Si on vous demande de décompresser `code.bin`, choisissez **No**.
4. Renommez le dossier `ExtractedRomFS` obtenu en `romfs-base`, déplacez ce dossier si vous le souhaitez.
5. Répétez les instruction 3 et 4 pour la mise à jour 1.3. En renommant le dossier comme `romfs-update` au lieu de `romfs-base`.
6. Vérifiez que chacun des deux dossiers contient un dossier `data/`, comme ceci:

   ```text
   romfs-base/data/
   romfs-update/data/
   ```

#### Méthode 2 - Via Azahar
> Pour cette méthode, vous aurez besoin d'avoir les jeu de base et mise à jour 1.3 installés sur Azahar.
1. Lancez Azahar
2. Faites un clic droit sur DQMJOKER3 PRO
3. Sélectionnez `Extraire RomFS`
4. Les RomFS des jeu de base et mise à jour 1.3 seront extraits et leur dossiers seront ouverts
5. Renommez les dossiers `0004000E001ACB00` en `romfs-base` et `0004000E001ACB00` en `romfs-update`, puis déplacez-les si vous le souhaitez.

#### Méthode 3 - Via GodMode9
> Pour cette méthode, vous aurez besoin d'avoir les jeu de base et mise à jour 1.3 installés sur votre 3DS avec CFW (Luma3DS).

> Note: Les instructions suivantes sont en français avec les commandes de gm9 en français, allez voir [ceci](https://github.com/d0k3/GodMode9#fonts-and-translations) pour installer la traduction française.
1. Allumez votre 3DS et appuyez sur **START** pour lancer Godmode9
2. Appuyez sur le bouton **HOME**
3. Sélectionnez `Gestionnaire d'applications`
4. Sélectionnez `[A] CARTE SD`
5. Descendez jusqu'à `00040000001ACB00 DQMJOKER3 PRO (CTR-U-BDQJ) (J) (v0.0.0)` et appuyez sur A
6. Sélectionnez `Ouvrir le dossier de l'app`
7. Sélectionnez le fichier qui finit en `.tmd` et appuyez sur **A**
8. Sélectionnez `Options de fichier TMD...` puis `Monter CXI/NDS sur le lecteur`
9. Appuyez sur **A**
10. Mettez le dossier `romfs` en sélection sans aller dedans
11. Appuyez sur **R** et **A**
12. Sélectionnez `Copier vers 0:/gm9/out`
13. Sélectionnez `[0:] CARTE SD` et allez dans `/gm9/out`
14. Mettez le dossier `romfs` en sélection et appuyez sur **R** + **X** pour renommer ce dossier en `romfs-base`
15. Refaites les étapes 2 à 14 mais avec `0004000E001ACB00 DQMJOKER3 PRO (CTR-U-BDQJ) (J) (v3.0.0)` et en renommant le dossier `romfs` en `romfs-update`
16. Appuyez sur **START** pour redémarrer la console ou **START** + **R** pour l'éteindre
17. Récupérez les dossiers `romfs-base` et `romfs-update` sur votre ordinateur

### 🚀 Lancer l'application

> Vous aurez besoin de Python 3.10+ avec Tkinter (généralement inclus dans l'installation de base de Python).

Depuis le dossier de l'application, lancez:

```powershell
python randomizer_app.py
```

Choisissez **EN**, **IT** ou **FR** dans le coin en haut à droite pour changer la langue.

### 🎲 Créer un paquet

1. Sélectionnez les dossiers RomFS des jeu de base et mise à jour 1.3. (Faites attention à ne pas sélectionner leur sous-dossiers `data/`) Si vous ne les avez pas encore extraits, allez voir [Récupérer le dossier RomFS](#récupérer-le-dossier-romfs).
2. Vous pouvez changer les familles autorisées pour les remplacements. 
3. Choisissez les rangs autorisés. Si les deux filtres sont actifs, chaque remplacement doit respecter les deux.
4. Entrez une graine. Utilisez `0` pour en générer une aléatoire.
5. Si vous le souhaitez, **Affichez les paramètres avancés**. Survolez **ⓘ** pour plus d'informations.
6. En option, sélectionnez **Randomiser aussi le niveau (1–99)**.
7. En option, sélectionnez **Utiliser des sets de compétences aléatoires**.
8. En option, sélectionnez **Utiliser les espèces de monstres d'évènement et de boss comme remplacements**.
9. En option, sélectionnez **Aussi changer les entrées en dehors des rencontres en combat (expérimental)**.
10. Cliquez sur **Créer le paquet**. Le dossier et le fichier ZIP seront dans `output/`.

Les mêmes paramètres et la même graine appliquent toujours les mêmes changements aux entrées de combat. Les rencontres de la même espèce peuvent changer si elles utilisent des entrées différentes. Les rencontres qui partagent une entrée ont les mêmes remplacements. Si la randomisation des niveaux est activée, chaque entrée MONP sélectionnée reçoit aussi un niveau de 1 à 99 déterminé par la graine. Les entrées partagées gardent le même niveau.

Par défaut, chaque remplacement reçoit le set de compétences natif de sa nouvelle espèce. Les sets supplémentaires sont conservés, sans doublons. **Utiliser des sets de compétences aléatoires** attribue plutôt des sets aléatoires aux emplacements occupés, parmi ceux déjà présents dans les données du jeu. La même graine donne le même résultat, sans sets en double pour un monstre.

Les paquets contiennent les fichiers modifiés, un manifeste, un fichier de spoilers, un fichier de configuration, et ce README avec les étapes d'installation. L'application vérifie les deux dossiers RomFS avant de créer ce paquet. Aucun fichier venant du jeu n'est inclus dans les paquets créés.

### Installer le randomizer

#### Sur 3DS avec CFW (Luma3DS)

> Si vous n'avez pas Luma3DS sur votre console, suivez [ce guide](https://3ds.hacks.guide/fr_FR/) pour l'installer.

- Activer le *game patching* (requis):
   1. Éteignez votre 3DS.
   2. Appuyez sur **SELECT** quand vous l'allumez.
   3. Activez **Enable game patching**.
   4. Appuyez sur **START** pour sauvegarder.
- Installer le randomizer:
    1. Sur la carte SD de votre 3DS créez (si non-existant) le dossier `/luma/titles/00040000001ACB00/`.
    2. Copiez le dossier `romfs/` du paquet dans ce dossier.
        - Écrasez les fichiers déjà existants.

#### Sur PC ou Android avec Azahar 

> Le jeu et la mise à jour 1.3 doivent déjà être installés.

- PC

    1. Dans la liste des jeux d'Azahar, faites un clic droit sur DQMJ3P et sélectionnez **Open Mods Location**.
    2. Copiez le dossier `romfs/` du paquet dans ce dossier.
        - Écrasez les fichiers déjà existants.

- Android

    1. Ouvrez le dossier des données de Azahar avec un explorateur de fichiers.
    2. Créez `load/mods/00040000001ACB00/` si nécessaire.
    3. Copiez le dossier `romfs/` du paquet dans ce dossier.
        - Écrasez les fichiers déjà existants.

### Vérifer la présence du ou supprimer le randomizer

- Lancez le jeu pour vérifier la présence du randomizer.
- Pour retirer/supprimer le randomizer:
    - Retirez les fichiers listés dans le manifeste du paquet package manifest.
    - Ou alors, supprimez le dossier RomFS. (voir section d'installation au dessus pour savoir où chercher)


### ⌨️ Utiliser la console pour créer des paquets

> Les commandes suivantes sont des exemples d'utilisation.

```powershell
python randomize.py --base-romfs "C:\path\to\base-romfs" --update-romfs "C:\path\to\update-romfs" --seed 42
python randomize.py --base-romfs "C:\path\to\base-romfs" --update-romfs "C:\path\to\update-romfs" --seed 42 --randomize-skills
python randomize.py --base-romfs "C:\path\to\base-romfs" --update-romfs "C:\path\to\update-romfs" --seed 42 --include-special-donors --include-nonwild-instances --randomize-levels
python randomize.py --base-romfs "C:\path\to\base-romfs" --update-romfs "C:\path\to\update-romfs" --seed 42 --family slime --family material
python randomize.py --base-romfs "C:\path\to\base-romfs" --update-romfs "C:\path\to\update-romfs" --seed 42 --family slime --rank f --rank ss
```

Le randomizer applique des changements via les entrées de combat. Lancez `python randomize.py --help` pour voir tous les paramètres. Pour l'installation, allez voir [Installer le randomizer](#installer-le-randomizer).

### 📚 Documentation

- [Formats de fichiers et détails techniques](https://github.com/Lurpigi/DQMJ3P-Randomizer/blob/main/docs/FORMAT.md#français)

### 💬 Communautés

Joignez le [serveur Discord DQMJ3P](https://discord.com/invite/W5yRJpDd5e).  
Joignez le [serveur Discord DQFan](https://discord.gg/WxF5Rhz).
