# DQMJ3P Randomizer
[English](#english) · [Italiano](#italiano)


<a href="https://github.com/Lurpigi/DQMJ3P-Randomizer/releases/latest">
  <img src="https://img.shields.io/github/v/release/Lurpigi/DQMJ3P-Randomizer?display_name=tag" alt="Latest release / Ultima release">
</a>
<a href="https://github.com/Lurpigi/DQMJ3P-Randomizer/releases/latest/download/dqmj3p_randomizer_portable.zip">
  <img src="https://img.shields.io/github/downloads/Lurpigi/DQMJ3P-Randomizer/total?label=downloads" alt="Downloads / Download">
</a>

<p align="center">
  <img src="https://raw.githubusercontent.com/Lurpigi/DQMJ3P-Randomizer/main/img/img.png" alt="DQMJ3P Randomizer icon / Icona del DQMJ3P Randomizer" width="220">
</p>



## English

A small randomizer for *Dragon Quest Monsters: Joker 3 Professional*. Pick a seed to replace encounter monsters while keeping their size. Use the same seed and options to get the same results again.

For the English fan patch, see [DQMJ3P English Fixed](https://github.com/Akoi89/DQMJ3P-english-fixed).

### Get the RomFS folders

You need a `.cia` or `.3ds` file for the base game and another for update 1.3.

1. Download [HackingToolkit3DS v9](https://github.com/Asia81/HackingToolkit9DS/releases/tag/9) and extract its archive.
2. Put the base game file in the HackingToolkit folder and start the extraction option for its format (`.cia` or `.3ds`). When asked whether to decompress `code.bin`, choose **No**.
3. Rename or move the resulting `ExtractedRomFS` folder to `romfs-base`.
4. Repeat steps 2 and 3 for update 1.3. Rename or move its `ExtractedRomFS` folder to `romfs-update`.
5. Check that both folders contain `data/` at the top level:

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

Choose **IT** or **EN** in the top-right corner to switch the app language.

The app does not include game files and does not open CIA or 3DS files. It needs the already extracted RomFS folders for the base game and update 1.3. The app combines them while it runs, with update files taking precedence. Keep the app folder together when you move it.

### 🎲 Make a package

1. Select the base game RomFS folder and the update 1.3 RomFS folder. If you still need to extract them, follow [Get the RomFS folders](#get-the-romfs-folders).
2. Choose the families allowed for replacements. This filter limits the replacement pool; it does not change which original monsters are randomized.
3. Choose the allowed ranks. If you use both filters, a replacement must match both.
4. Enter a seed. Use `0` to get a random one.
5. Open **Advanced options** if needed. Hover over **ⓘ** for details.
6. Optional: select **Use event and boss species as replacements**.
7. Optional: select **Also change records outside wild encounters (experimental)**.
8. Click **Create package**. Find the folder and ZIP in `output/`.

The same seed and options always assign the same replacement to each battle record. Encounters of the same species can differ if they use different records. Encounters that share a record keep the same replacement.

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
python randomize.py --base-romfs "C:\path\to\base-romfs" --update-romfs "C:\path\to\update-romfs" --seed 42 --include-special-donors --include-nonwild-instances
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

Un piccolo randomizer per *Dragon Quest Monsters: Joker 3 Professional*. Scegli un seed per sostituire i mostri degli incontri mantenendone la taglia. Usa lo stesso seed e le stesse opzioni per ottenere di nuovo gli stessi risultati.

### Ottieni le cartelle RomFS

Servono un file `.cia` o `.3ds` del gioco base e un altro dell'aggiornamento 1.3.

1. Scarica [HackingToolkit3DS v9](https://github.com/Asia81/HackingToolkit9DS/releases/tag/9) ed estrai l'archivio.
2. Metti il file del gioco base nella cartella di HackingToolkit e avvia l'estrazione per il suo formato (`.cia` o `.3ds`). Quando ti chiede se decomprimere `code.bin`, scegli **No**.
3. Rinomina o sposta la cartella `ExtractedRomFS` ottenuta in `romfs-base`.
4. Ripeti i passaggi 2 e 3 per l'aggiornamento 1.3. Rinomina o sposta la sua cartella `ExtractedRomFS` in `romfs-update`.
5. Controlla che entrambe le cartelle contengano `data/` al loro interno:

   ```text
   romfs-base/data/
   romfs-update/data/
   ```

Nell'app, seleziona `romfs-base` e `romfs-update`, non le sottocartelle `data/`.

### 🚀 Avvio

Serve Python 3.10 o versioni successive con Tkinter. Dalla cartella del programma, esegui:

```powershell
python randomizer_app.py
```

Scegli **IT** o **EN** in alto a destra per cambiare la lingua dell'app.

L'app non include file di gioco e non apre file CIA o 3DS. Richiede le cartelle RomFS già estratte del gioco base e dell'aggiornamento 1.3. Le combina mentre è in esecuzione e dà precedenza ai file dell'update. Quando sposti l'app, conserva tutta la cartella.

### 🎲 Crea un pacchetto

1. Seleziona la cartella RomFS del gioco base e quella dell'aggiornamento 1.3. Se devi ancora estrarle, segui [Ottieni le cartelle RomFS](#ottieni-le-cartelle-romfs).
2. Scegli le famiglie ammesse per i sostituti. Il filtro limita il pool dei sostituti, ma non cambia quali mostri originali vengono randomizzati.
3. Scegli i gradi ammessi. Se usi entrambi i filtri, ogni sostituto deve rispettarli entrambi.
4. Inserisci un seed. Usa `0` per generarne uno casuale.
5. Apri **Opzioni avanzate** se ti servono. Passa il puntatore su **ⓘ** per i dettagli.
6. Facoltativo: seleziona **Usa specie di eventi e boss come sostituti**.
7. Facoltativo: seleziona **Modifica anche i record fuori dagli incontri selvatici (sperimentale)**.
8. Premi **Crea pacchetto**. Trovi la cartella e il file ZIP in `output/`.

Lo stesso seed e le stesse opzioni assegnano sempre lo stesso sostituto a ogni record di battaglia. Incontri della stessa specie possono essere diversi se usano record diversi. Gli incontri che condividono un record mantengono lo stesso sostituto.

Il pacchetto contiene i file modificati, un manifest, uno spoiler, una configurazione e questo README con le istruzioni d'installazione. Prima di crearlo, l'app controlla entrambe le cartelle selezionate. Il download dell'app non contiene file di gioco.

### Installa la mod

**3DS con Luma3DS**

1. Spegni il 3DS. Tieni premuto **SELECT** mentre lo accendi, attiva **Enable game patching** e premi **START** per salvare.
2. Sulla scheda SD, crea `/luma/titles/00040000001ACB00/romfs/`.
3. Copia in questa cartella il contenuto di `romfs/` dello ZIP del randomizer. Sostituisci i file omonimi.
4. Reinserisci la scheda SD nel 3DS e avvia il gioco.

**Azahar su PC o Android**

Installa prima in Azahar il gioco e l'aggiornamento 1.3.

PC:

1. Nell'elenco dei giochi di Azahar, fai clic destro sul gioco e scegli **Open Mods Location**.
2. Se non esiste, crea la cartella `romfs/` nella cartella della mod.
3. Copia al suo interno il contenuto di `romfs/` dello ZIP del randomizer. Sostituisci i file omonimi.

Android:

1. Apri la cartella dei dati di Azahar con un gestore file.
2. Crea `load/mods/00040000001ACB00/romfs/`.
3. Copia in questa cartella il contenuto di `romfs/` dello ZIP del randomizer.

### Controlla o rimuovi la mod

Avvia il gioco e rientra in una zona per aggiornare gli incontri. Per rimuovere il randomizer, elimina i file elencati nel manifest del pacchetto.


### ⌨️ Usa la riga di comando

```powershell
python randomize.py --base-romfs "C:\percorso\romfs-base" --update-romfs "C:\percorso\romfs-update" --seed 42
python randomize.py --base-romfs "C:\percorso\romfs-base" --update-romfs "C:\percorso\romfs-update" --seed 42 --include-special-donors --include-nonwild-instances
python randomize.py --base-romfs "C:\percorso\romfs-base" --update-romfs "C:\percorso\romfs-update" --seed 42 --family slime --family material
python randomize.py --base-romfs "C:\percorso\romfs-base" --update-romfs "C:\percorso\romfs-update" --seed 42 --family slime --rank f --rank ss
```

Il randomizer assegna i sostituti in base al record di battaglia. Esegui `python randomize.py --help` per vedere tutte le opzioni. Per l'installazione, consulta [Installa la mod](#installa-la-mod). Per i dettagli tecnici, consulta [FORMAT.md](https://github.com/Lurpigi/DQMJ3P-Randomizer/blob/main/docs/FORMAT.md#italiano).

### 📚 Guide

- [Formati e dettagli tecnici](https://github.com/Lurpigi/DQMJ3P-Randomizer/blob/main/docs/FORMAT.md#italiano)

### 💬 Comunità

Entra nel [server Discord di DQMJ3P](https://discord.com/invite/W5yRJpDd5e).
