# Install the randomizer / Installa il randomizer

[English](#english) · [Italiano](#italiano)

## English

This guide explains how to create and install a randomizer package. You need the game and update 1.3. The package does not include them or a fan translation. For English, see [DQMJ3P English Fixed](https://github.com/Akoi89/DQMJ3P-english-fixed). For Italian, install the [fan translation](https://github.com/Lurpigi/DQMJ3P-IT-FanTranslation) first.

### Extract the RomFS folders

You need a `.cia` or `.3ds` file for the base game and another for update 1.3.

1. Download [HackingToolkit3DS v9](https://github.com/Asia81/HackingToolkit9DS/releases/tag/9) and extract its archive.
2. Put the base game file in the HackingToolkit folder and start the extraction option for its format (`.cia` or `.3ds`). When asked whether to decompress `code.bin`, choose **No**.
3. Rename or move the resulting `ExtractedRomFS` folder to `romfs-base`.
4. Repeat steps 2 and 3 for update 1.3. Rename or move the new `ExtractedRomFS` folder to `romfs-update`.
5. Check that both folders contain `data/` at the top level:

   ```text
   romfs-base/data/
   romfs-update/data/
   ```

In the app, select `romfs-base` and `romfs-update`, not their `data/` subfolders.

### How the app uses these folders

The app combines the two folders while it runs. If both contain the same file, it uses the update's copy. It does not change the source folders. See [FORMAT.md](FORMAT.md#english) for details.

### Create a package

1. Run `python randomizer_app.py` from the program folder.
2. Select the base game RomFS and update 1.3 RomFS folders.
3. Choose the families and ranks allowed for replacements. All options are selected by default. When both filters are used, replacements must match both.
4. Enter a seed. Enter `0` for a random seed.
5. Choose any advanced options, then click **Create package**.
6. Find the package folder and ZIP in `output/`.

### Install on a 3DS with Luma3DS

1. Turn off the 3DS. Hold **SELECT** while turning it on, enable **Enable game patching**, then press **START** to save.
2. On the SD card, create `/luma/titles/00040000001ACB00/romfs/`.
3. If using the Italian translation, copy the contents of `main_it/` and `update_it/` into this `romfs/` folder.
4. Copy the randomizer ZIP's `romfs/` contents into the same folder. Replace matching files.
5. For the translation's technical patch, copy `exefs/code.ips` beside the `romfs/` folder as `code.ips`.
6. Put the SD card back in the 3DS and start the game.

### Install in Azahar on PC or Android

Install the game and update 1.3 in Azahar first. The translation guide also lists Lime3DS-DQMJ3P and Citra nightly 1543 or earlier.

**PC**

1. In Azahar's game list, right-click the game and choose **Open Mods Location**.
2. Copy the translation files, if used, into the mod's `romfs/` folder: copy `main_it/` first, then `update_it/`.
3. Copy the randomizer ZIP's `romfs/` contents into that same folder and replace matching files.
4. Copy the translation's `exefs/code.ips` into the mod's `exefs/` folder.

**Android**

1. Open Azahar's data folder with a file manager.
2. Create `load/mods/00040000001ACB00/romfs/` and `load/mods/00040000001ACB00/exefs/`.
3. If using the translation, copy `main_it/` and then `update_it/` into `romfs/`.
4. Copy the randomizer ZIP's `romfs/` contents into the same folder. Copy `exefs/code.ips` into `exefs/`.

Keep the paths inside `romfs/`; do not create `romfs/main_it/` or `romfs/update_it/`. In emulators, `code.ips` belongs in `exefs/` under the main game's Title ID, `00040000001ACB00`.

### Check or remove the mod

Start the game and revisit an area to refresh its encounters. To remove the randomizer, delete the files listed in the package manifest. Keep the translation files if you still use them.

## Italiano

Questa guida spiega come creare e installare un pacchetto del randomizer. Servono il gioco e l'aggiornamento 1.3. Il pacchetto non include il gioco, l'update o la traduzione italiana. Per giocare in italiano, installa prima la [traduzione amatoriale](https://github.com/Lurpigi/DQMJ3P-IT-FanTranslation).

### Estrai le cartelle RomFS

Servono un file `.cia` o `.3ds` del gioco base e un altro dell'aggiornamento 1.3.

1. Scarica [HackingToolkit3DS v9](https://github.com/Asia81/HackingToolkit9DS/releases/tag/9) ed estrai l'archivio.
2. Metti il file del gioco base nella cartella di HackingToolkit e avvia l'estrazione per il suo formato (`.cia` o `.3ds`). Quando ti chiede se decomprimere `code.bin`, scegli **No**.
3. Rinomina o sposta la cartella `ExtractedRomFS` ottenuta in `romfs-base`.
4. Ripeti i passaggi 2 e 3 per l'aggiornamento 1.3. Rinomina o sposta la nuova cartella `ExtractedRomFS` in `romfs-update`.
5. Controlla che entrambe le cartelle contengano `data/` al loro interno:

   ```text
   romfs-base/data/
   romfs-update/data/
   ```

Nell'app, seleziona `romfs-base` e `romfs-update`, non le sottocartelle `data/`.

### Come usa queste cartelle l'app

L'app combina le due cartelle mentre è in esecuzione. Se un file è presente in entrambe, usa quello dell'update. Non modifica le cartelle sorgenti. Per i dettagli, consulta [FORMAT.md](FORMAT.md#italiano).

### Crea un pacchetto

1. Esegui `python randomizer_app.py` dalla cartella del programma.
2. Seleziona il RomFS del gioco base e quello dell'aggiornamento 1.3.
3. Scegli le famiglie e i gradi ammessi per i sostituti. All'inizio sono selezionati tutti. Se usi entrambi i filtri, i sostituti devono corrispondere a entrambi.
4. Inserisci un seed. Usa `0` per generarne uno casuale.
5. Scegli le opzioni avanzate che vuoi e premi **Crea pacchetto**.
6. Trovi la cartella e il file ZIP in `output/`.

### Installa su 3DS con Luma3DS

1. Spegni il 3DS. Tieni premuto **SELECT** mentre lo accendi, attiva **Enable game patching** e premi **START** per salvare.
2. Sulla scheda SD, crea `/luma/titles/00040000001ACB00/romfs/`.
3. Se usi la traduzione italiana, copia in `romfs/` il contenuto di `main_it/` e poi quello di `update_it/`.
4. Copia nella stessa cartella il contenuto di `romfs/` dello ZIP del randomizer. Sostituisci i file omonimi.
5. Per la patch tecnica della traduzione, copia `exefs/code.ips` accanto alla cartella `romfs/` e chiamalo `code.ips`.
6. Reinserisci la scheda SD nel 3DS e avvia il gioco.

### Installa in Azahar su PC o Android

Installa prima in Azahar il gioco e l'aggiornamento 1.3. La guida della traduzione indica anche Lime3DS-DQMJ3P e Citra nightly 1543 o versioni precedenti.

**PC**

1. Nell'elenco dei giochi di Azahar, fai clic destro sul gioco e scegli **Open Mods Location**.
2. Se usi la traduzione, copia i suoi file nella cartella `romfs/` della mod: prima `main_it/`, poi `update_it/`.
3. Copia nella stessa cartella il contenuto di `romfs/` dello ZIP del randomizer e sostituisci i file omonimi.
4. Copia `exefs/code.ips` della traduzione nella cartella `exefs/` della mod.

**Android**

1. Apri la cartella dei dati di Azahar con un gestore file.
2. Crea `load/mods/00040000001ACB00/romfs/` e `load/mods/00040000001ACB00/exefs/`.
3. Se usi la traduzione, copia in `romfs/` prima `main_it/` e poi `update_it/`.
4. Copia nella stessa cartella il contenuto di `romfs/` dello ZIP del randomizer. Copia `exefs/code.ips` in `exefs/`.

Mantieni i percorsi dentro `romfs/`: non creare `romfs/main_it/` o `romfs/update_it/`. Negli emulatori, `code.ips` va in `exefs/` sotto il Title ID principale, `00040000001ACB00`.

### Controlla o rimuovi la mod

Avvia il gioco e rientra in una zona per aggiornare gli incontri. Per rimuovere il randomizer, elimina i file elencati nel manifest del pacchetto. Conserva i file della traduzione se li usi ancora.
