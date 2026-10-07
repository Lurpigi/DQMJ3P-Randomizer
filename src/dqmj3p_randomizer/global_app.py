"""Tkinter app for per-record encounter randomization."""

from __future__ import annotations

import secrets
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .global_catalog import GlobalCatalogError, RANK_CODES, parse_kind_catalog
from .global_service import GlobalBuildError, build_global_overlay
from .romfs_source import RomFsSource, RomFsSourceError


FAMILY_ICONS = {
    1: "💧", 2: "🐉", 3: "🐾", 4: "🌿", 5: "😈",
    6: "💀", 7: "⚙️",
}
FAMILY_LABELS = {
    "it": {
        1: "Slime", 2: "Drago", 3: "Bestia", 4: "Natura", 5: "Demone",
        6: "Non-morti", 7: "Materiale", 8: "Corrotti", 9: "???",
    },
    "en": {
        1: "Slime", 2: "Dragon", 3: "Beast", 4: "Nature", 5: "Demon",
        6: "Undead", 7: "Material", 8: "Break", 9: "???",
    },
}


class ToolTip:
    def __init__(self, widget: ttk.Label, text: str, wraplength: int = 360) -> None:
        self.widget = widget
        self.text = text
        self.wraplength = wraplength
        self.tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self.show, add="+")
        widget.bind("<Leave>", self.hide, add="+")
        widget.bind("<FocusIn>", self.show, add="+")
        widget.bind("<FocusOut>", self.hide, add="+")
        widget.bind("<KeyPress-Escape>", self.hide, add="+")
        widget.bind("<KeyPress-Return>", self.show, add="+")
        widget.bind("<KeyPress-space>", self.show, add="+")
        widget.bind("<Destroy>", self._on_widget_destroy, add="+")

    def show(self, _event=None) -> None:
        if self.tip is not None or not self.text:
            return
        try:
            tip = tk.Toplevel(self.widget)
            self.tip = tip
            tip.wm_overrideredirect(True)
            tip.withdraw()
            if sys.platform == "darwin":
                try:
                    tip.wm_attributes("-topmost", True)
                    tip.lift()
                    tip.transient(self.widget.winfo_toplevel())
                except tk.TclError:
                    pass
            tk.Label(
                tip, text=self.text, justify="left", foreground="black", background="#ffffe0",
                relief="solid", borderwidth=1, padx=6, pady=4,
                wraplength=self.wraplength,
            ).pack()
            tip.update_idletasks()
            x = self.widget.winfo_rootx() + 18
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
            x = max(0, min(x, tip.winfo_screenwidth() - tip.winfo_reqwidth()))
            y = max(0, min(y, tip.winfo_screenheight() - tip.winfo_reqheight()))
            tip.wm_geometry(f"+{x}+{y}")
            tip.deiconify()
            tip.lift()
            tip.update_idletasks()
        except tk.TclError:
            self.hide()

    def hide(self, _event=None) -> None:
        tip, self.tip = self.tip, None
        if tip is not None:
            try:
                tip.destroy()
            except tk.TclError:
                pass

    def _on_widget_destroy(self, event) -> None:
        if event.widget is self.widget:
            self.hide()


def add_info_icon(parent: ttk.Frame, text: str) -> ttk.Label:
    icon = ttk.Label(parent, text="\u24d8", cursor="question_arrow",
                     foreground="blue", takefocus=True)
    icon.tooltip = ToolTip(icon, text)
    return icon


_TEXT = {
    "it": {
        "window_title": "Randomizer DQMJ3P",
        "app_title": "Randomizer degli incontri DQMJ3P",
        "subtitle": "Sostituisce i mostri e ne mantiene la taglia.",
        "choose_base_romfs": "Seleziona RomFS del gioco base",
        "choose_update_romfs": "Seleziona RomFS dell'update 1.3",
        "base_not_selected": "Cartella base non selezionata",
        "update_not_selected": "Cartella update non selezionata",
        "base_romfs_dialog_title": "Seleziona il RomFS estratto del gioco base",
        "update_romfs_dialog_title": "Seleziona il RomFS estratto dell'update 1.3",
        "select_romfs": "Seleziona le cartelle RomFS estratte del gioco base e dell'update 1.3.",
        "select_base_romfs": "Seleziona la cartella RomFS del gioco base.",
        "select_update_romfs": "Seleziona la cartella RomFS dell'update 1.3.",
        "families": "Famiglie dei sostituti",
        "family_description": "Limita il pool dei sostituti. Se scegli anche un grado, valgono entrambi i filtri.",
        "select_all_families": "Seleziona tutte",
        "families_not_loaded": "Seleziona le cartelle RomFS per caricare le famiglie.",
        "family_error_title": "Nessuna famiglia di sostituti selezionata",
        "no_family_selected": "Seleziona almeno una famiglia per i sostituti.",
        "ranks": "Gradi dei sostituti",
        "rank_description": "I filtri non cambiano quali mostri originali vengono randomizzati.",
        "select_all_ranks": "Seleziona tutti",
        "ranks_not_loaded": "Seleziona le cartelle RomFS per caricare i gradi.",
        "rank_error_title": "Nessun grado di sostituti selezionato",
        "no_rank_selected": "Seleziona almeno un grado per i sostituti.",
        "seed": "Seed",
        "random_seed": "Inserisci 0 per un seed casuale",
        "show_advanced": "Mostra opzioni avanzate",
        "hide_advanced": "Nascondi opzioni avanzate",
        "advanced": "Opzioni avanzate",
        "special_option": "Usa specie di eventi e boss come sostituti",
        "special_help": "Aggiunge specie di eventi e boss con taglia e modello compatibili. L'opzione seguente estende le modifiche ai record fuori dagli incontri selvatici. Alcuni record sono condivisi con gli incontri selvatici.",
        "nonwild_option": "Modifica anche i record fuori dagli incontri selvatici (sperimentale)",
        "nonwild_help": "Estende le modifiche ai record MONP fuori dagli incontri selvatici. Può coinvolgere eventi, boss, personaggi e tornei. Alcune scene possono mostrare ancora il mostro originale.",
        "create": "Crea pacchetto",
        "ready": "Cartelle pronte: trovati {count} archivi degli incontri.",
        "data_error": "Le cartelle RomFS non sono valide o sono incomplete.",
        "building": "Analisi delle tabelle e creazione del pacchetto…",
        "build_error": "Creazione non riuscita.",
        "created": "Pacchetto creato (seed {seed}): {path}",
        "data_error_title": "RomFS non disponibile",
        "invalid_title": "Seed non valido",
        "invalid_seed": "Inserisci un intero da 0 a 2⁶⁴−1.",
        "error_title": "Errore",
        "complete_title": "Completato",
        "complete_message": "Pacchetto creato:\n{path}\n\nSeed usato: {seed}\nEstrai lo ZIP e copia la cartella romfs.",
    },
    "en": {
        "window_title": "DQMJ3P Randomizer",
        "app_title": "DQMJ3P Encounter Randomizer",
        "subtitle": "Replace monsters while keeping their size.",
        "choose_base_romfs": "Select base game RomFS",
        "choose_update_romfs": "Select update 1.3 RomFS",
        "base_not_selected": "Base folder not selected",
        "update_not_selected": "Update folder not selected",
        "base_romfs_dialog_title": "Select the extracted base game RomFS",
        "update_romfs_dialog_title": "Select the extracted update 1.3 RomFS",
        "select_romfs": "Select the extracted base game and update 1.3 RomFS folders.",
        "select_base_romfs": "Select the base game RomFS folder.",
        "select_update_romfs": "Select the update 1.3 RomFS folder.",
        "families": "Replacement families",
        "family_description": "Limits the replacement pool. If you also choose a rank, both filters apply.",
        "select_all_families": "Select all",
        "families_not_loaded": "Select the RomFS folders to load the families.",
        "family_error_title": "No replacement family selected",
        "no_family_selected": "Select at least one replacement family.",
        "ranks": "Replacement ranks",
        "rank_description": "These filters do not affect which original monsters are randomized.",
        "select_all_ranks": "Select all",
        "ranks_not_loaded": "Select the RomFS folders to load the ranks.",
        "rank_error_title": "No replacement rank selected",
        "no_rank_selected": "Select at least one replacement rank.",
        "seed": "Seed",
        "random_seed": "Enter 0 for a random seed",
        "show_advanced": "Show advanced options",
        "hide_advanced": "Hide advanced options",
        "advanced": "Advanced options",
        "special_option": "Use event and boss species as replacements",
        "special_help": "Adds event and boss species with a compatible size and model. The next option also changes records outside wild encounters. Some records are shared with wild encounters.",
        "nonwild_option": "Also change records outside wild encounters (experimental)",
        "nonwild_help": "Extends changes to MONP records outside wild encounters. This may affect events, bosses, characters, and tournaments. Some scenes may still show the original monster.",
        "create": "Create package",
        "ready": "Folders ready: found {count} encounter archives.",
        "data_error": "The RomFS folders are invalid or incomplete.",
        "building": "Reading tables and creating package…",
        "build_error": "Could not create the package.",
        "created": "Package created (seed {seed}): {path}",
        "data_error_title": "RomFS unavailable",
        "invalid_title": "Invalid seed",
        "invalid_seed": "Enter an integer from 0 to 2⁶⁴−1.",
        "error_title": "Error",
        "complete_title": "Done",
        "complete_message": "Package created:\n{path}\n\nSeed: {seed}\nExtract the ZIP and copy the romfs folder.",
    },
}


class GlobalRandomizerApp:
    def __init__(self, root: tk.Tk | None = None) -> None:
        self.root = root or tk.Tk()
        self.project = Path(__file__).resolve().parents[2]
        self.root.minsize(700, 470)
        icon = tk.PhotoImage(file=str(self.project / "img" / "img.png"))
        scale = max(1, (max(icon.width(), icon.height()) + 255) // 256)
        self._window_icon = icon.subsample(scale, scale) if scale > 1 else icon
        self.root.iconphoto(True, self._window_icon)

        self.language_var = tk.StringVar(value="it")
        self.seed_var = tk.StringVar(
            value=str(secrets.randbelow(2**64 - 1) + 1))
        self.special_var = tk.BooleanVar(value=False)
        self.nonwild_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="")
        self.advanced_open = False
        self.dataset_available = False
        self.dataset_archive_count = 0
        self.base_romfs_root: Path | None = None
        self.update_romfs_root: Path | None = None
        self.base_romfs_path_var = tk.StringVar(value="")
        self.update_romfs_path_var = tk.StringVar(value="")
        self.available_family_codes: tuple[int, ...] = ()
        self.family_vars: dict[int, tk.BooleanVar] = {}
        self.family_checkbuttons: dict[int, ttk.Checkbutton] = {}
        self.available_rank_codes: tuple[int, ...] = ()
        self.rank_vars: dict[int, tk.BooleanVar] = {}
        self.rank_checkbuttons: dict[int, ttk.Checkbutton] = {}
        self.is_building = False
        self.status_key = "select_romfs"
        self.status_values: dict[str, object] = {}
        self.advanced_options: list[tuple[ttk.Checkbutton, ToolTip, str, str]] = []

        self._build_widgets()
        self._refresh_language()

    def _text(self, key: str) -> str:
        return _TEXT[self.language_var.get()][key]

    def _build_widgets(self) -> None:
        outer = ttk.Frame(self.root, padding=20)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x")
        self.title_label = ttk.Label(
            header, font=("Segoe UI", 16, "bold"))
        self.title_label.pack(side="left", anchor="w")
        self._build_language_picker(header)

        self.subtitle_label = ttk.Label(outer, wraplength=560)
        self.subtitle_label.pack(anchor="w", pady=(5, 20))

        romfs_row = ttk.Frame(outer)
        romfs_row.pack(fill="x", pady=(0, 16))
        romfs_row.columnconfigure(0, weight=1)
        romfs_row.columnconfigure(1, weight=1)
        self.base_romfs_button = ttk.Button(
            romfs_row, command=lambda: self._select_romfs("base"))
        self.base_romfs_button.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.update_romfs_button = ttk.Button(
            romfs_row, command=lambda: self._select_romfs("update"))
        self.update_romfs_button.grid(row=0, column=1, sticky="w")
        self.base_romfs_path_label = ttk.Label(
            romfs_row, textvariable=self.base_romfs_path_var, wraplength=310)
        self.base_romfs_path_label.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(5, 0))
        self.update_romfs_path_label = ttk.Label(
            romfs_row, textvariable=self.update_romfs_path_var, wraplength=310)
        self.update_romfs_path_label.grid(row=1, column=1, sticky="ew", pady=(5, 0))

        self.family_group = ttk.LabelFrame(outer, padding=10)
        self.family_group.pack(fill="x", pady=(0, 12))
        family_header = ttk.Frame(self.family_group)
        family_header.pack(fill="x")
        self.family_description_label = ttk.Label(
            family_header, wraplength=470, justify="left")
        self.family_description_label.pack(side="left", fill="x", expand=True)
        self.select_all_families_button = ttk.Button(
            family_header, command=self._select_all_families)
        self.select_all_families_button.pack(side="right", padx=(8, 0))
        self.family_options_frame = ttk.Frame(self.family_group)
        self.family_options_frame.pack(fill="x", pady=(8, 0))
        self.family_empty_label = ttk.Label(self.family_group)
        self.family_empty_label.pack(anchor="w")

        self.rank_group = ttk.LabelFrame(outer, padding=10)
        self.rank_group.pack(fill="x", pady=(0, 12))
        rank_header = ttk.Frame(self.rank_group)
        rank_header.pack(fill="x")
        self.rank_description_label = ttk.Label(
            rank_header, wraplength=470, justify="left")
        self.rank_description_label.pack(side="left", fill="x", expand=True)
        self.select_all_ranks_button = ttk.Button(
            rank_header, command=self._select_all_ranks)
        self.select_all_ranks_button.pack(side="right", padx=(8, 0))
        self.rank_options_frame = ttk.Frame(self.rank_group)
        self.rank_options_frame.pack(fill="x", pady=(8, 0))
        self.rank_empty_label = ttk.Label(self.rank_group)
        self.rank_empty_label.pack(anchor="w")

        seed_row = ttk.Frame(outer)
        seed_row.pack(fill="x")
        self.seed_label = ttk.Label(seed_row)
        self.seed_label.pack(side="left")
        self.seed_entry = ttk.Entry(
            seed_row, textvariable=self.seed_var, width=28)
        self.seed_entry.pack(side="left", padx=(12, 8))
        self.random_seed_label = ttk.Label(seed_row)
        self.random_seed_label.pack(side="left")

        self.advanced_button = ttk.Button(
            outer, command=self._toggle_advanced)
        self.advanced_button.pack(anchor="w", pady=(20, 8))
        self.advanced = ttk.LabelFrame(outer, padding=10)
        self.advanced.pack_propagate(True)
        self._build_advanced()

        self.generate_button = ttk.Button(
            outer, command=self._start_build)
        self.generate_button.pack(anchor="w", pady=(20, 8))
        self.status_label = ttk.Label(
            outer, textvariable=self.status_var, wraplength=560)
        self.status_label.pack(fill="x", anchor="w")

    def _build_language_picker(self, parent: ttk.Frame) -> None:
        picker = ttk.Frame(parent)
        picker.pack(side="right", padx=(8, 0))
        for language, label in (("it", "IT"), ("en", "EN")):
            option = ttk.Frame(picker)
            option.pack(side="left", padx=(0, 4))
            flag = tk.Canvas(
                option, width=24, height=16, highlightthickness=0,
                borderwidth=0, cursor="hand2")
            self._draw_flag(flag, language)
            flag.pack(side="left", padx=(0, 3))
            flag.bind(
                "<Button-1>",
                lambda _event, value=language: self._select_language(value),
            )
            ttk.Radiobutton(
                option, text=label, value=language,
                variable=self.language_var, command=self._refresh_language,
            ).pack(side="left")

    @staticmethod
    def _draw_flag(canvas: tk.Canvas, language: str) -> None:
        if language == "it":
            canvas.create_rectangle(0, 0, 8, 16, fill="#009246", outline="")
            canvas.create_rectangle(8, 0, 16, 16, fill="#ffffff", outline="")
            canvas.create_rectangle(16, 0, 24, 16, fill="#ce2b37", outline="")
            return

        canvas.create_rectangle(0, 0, 24, 16, fill="#012169", outline="#888888")
        canvas.create_line(0, 0, 24, 16, fill="#ffffff", width=5)
        canvas.create_line(0, 16, 24, 0, fill="#ffffff", width=5)
        canvas.create_line(0, 0, 24, 16, fill="#c8102e", width=2)
        canvas.create_line(0, 16, 24, 0, fill="#c8102e", width=2)
        canvas.create_line(12, 0, 12, 16, fill="#ffffff", width=7)
        canvas.create_line(0, 8, 24, 8, fill="#ffffff", width=7)
        canvas.create_line(12, 0, 12, 16, fill="#c8102e", width=4)
        canvas.create_line(0, 8, 24, 8, fill="#c8102e", width=4)

    def _select_language(self, language: str) -> None:
        self.language_var.set(language)
        self._refresh_language()

    def _family_label(self, code: int) -> str:
        return FAMILY_LABELS[self.language_var.get()].get(
            code,
            f"Family {code}" if self.language_var.get() == "en" else f"Famiglia {code}",
        )

    def _family_icon_widget(self, parent: ttk.Frame, code: int) -> tk.Widget:
        if code not in {8, 9}:
            return ttk.Label(
                parent, text=FAMILY_ICONS.get(code, "◇"),
                font=("Segoe UI Emoji", 13), width=3, anchor="center")

        canvas = tk.Canvas(
            parent, width=30, height=26, highlightthickness=0,
            borderwidth=0, background=self.root.cget("background"))
        if code == 8:
            # Purple crystal for the Break family.
            canvas.create_polygon(
                15, 2, 26, 8, 23, 19, 15, 24, 7, 19, 4, 8,
                fill="#8538c9", outline="#4c1d78", width=1)
            canvas.create_polygon(15, 2, 11, 8, 15, 21, 7, 19, 4, 8,
                                 fill="#b86cf0", outline="")
            canvas.create_polygon(15, 2, 19, 8, 15, 21, 23, 19, 26, 8,
                                 fill="#62269b", outline="")
            canvas.create_polygon(11, 8, 19, 8, 15, 21,
                                 fill="#d5a0ff", outline="")
        else:
            # Gold crown for the unknown family.
            canvas.create_polygon(
                3, 8, 9, 14, 15, 4, 21, 14, 27, 8, 24, 20, 6, 20,
                fill="#f2bf38", outline="#9a6800", width=1)
            canvas.create_rectangle(
                6, 20, 24, 23, fill="#e6a91c", outline="#9a6800", width=1)
            for x, y in ((3, 7), (15, 3), (27, 7)):
                canvas.create_oval(
                    x - 2, y - 2, x + 2, y + 2,
                    fill="#ffd85a", outline="#9a6800", width=1)
        return canvas

    def _render_family_options(self, family_codes: tuple[int, ...]) -> None:
        previous_codes = set(self.family_vars)
        previously_selected = {
            code for code, variable in self.family_vars.items() if variable.get()
        }
        had_options = bool(previous_codes)
        for child in self.family_options_frame.winfo_children():
            child.destroy()
        self.family_vars = {}
        self.family_checkbuttons = {}
        self.available_family_codes = family_codes

        if not family_codes:
            self.family_empty_label.configure(text=self._text("families_not_loaded"))
            self.family_empty_label.pack(anchor="w")
            return
        self.family_empty_label.pack_forget()

        for column in range(3):
            self.family_options_frame.columnconfigure(column, weight=1)
        for index, code in enumerate(family_codes):
            cell = ttk.Frame(self.family_options_frame)
            cell.grid(row=index // 3, column=index % 3, sticky="w", padx=(0, 10), pady=2)
            icon = self._family_icon_widget(cell, code)
            icon.pack(side="left")
            initially_selected = (
                code in previously_selected or code not in previous_codes
                if had_options else True
            )
            variable = tk.BooleanVar(value=initially_selected)
            checkbutton = ttk.Checkbutton(
                cell, text=self._family_label(code), variable=variable,
                command=self._refresh_language)
            checkbutton.pack(side="left")
            self.family_vars[code] = variable
            self.family_checkbuttons[code] = checkbutton

    def _render_rank_options(self, rank_codes: tuple[int, ...]) -> None:
        previous_codes = set(self.rank_vars)
        previously_selected = {
            code for code, variable in self.rank_vars.items() if variable.get()
        }
        had_options = bool(previous_codes)
        for child in self.rank_options_frame.winfo_children():
            child.destroy()
        self.rank_vars = {}
        self.rank_checkbuttons = {}
        self.available_rank_codes = rank_codes

        if not rank_codes:
            self.rank_empty_label.configure(text=self._text("ranks_not_loaded"))
            self.rank_empty_label.pack(anchor="w")
            return
        self.rank_empty_label.pack_forget()

        for column in range(4):
            self.rank_options_frame.columnconfigure(column, weight=1)
        for index, code in enumerate(rank_codes):
            cell = ttk.Frame(self.rank_options_frame)
            cell.grid(row=index // 4, column=index % 4, sticky="w", padx=(0, 10), pady=2)
            initially_selected = (
                code in previously_selected or code not in previous_codes
                if had_options else True
            )
            variable = tk.BooleanVar(value=initially_selected)
            checkbutton = ttk.Checkbutton(
                cell, text=RANK_CODES.get(code, f"Rank {code}"), variable=variable,
                command=self._refresh_language)
            checkbutton.pack(side="left")
            self.rank_vars[code] = variable
            self.rank_checkbuttons[code] = checkbutton

    def _selected_family_codes(self) -> frozenset[int]:
        return frozenset(
            code for code, variable in self.family_vars.items() if variable.get()
        )

    def _donor_family_codes(self) -> frozenset[int] | None:
        selected = self._selected_family_codes()
        if selected == frozenset(self.available_family_codes):
            return None
        return selected

    def _select_all_families(self) -> None:
        for variable in self.family_vars.values():
            variable.set(True)
        self._refresh_language()

    def _selected_rank_codes(self) -> frozenset[int]:
        return frozenset(
            code for code, variable in self.rank_vars.items() if variable.get()
        )

    def _donor_rank_codes(self) -> frozenset[int] | None:
        selected = self._selected_rank_codes()
        if selected == frozenset(self.available_rank_codes):
            return None
        return selected

    def _select_all_ranks(self) -> None:
        for variable in self.rank_vars.values():
            variable.set(True)
        self._refresh_language()

    def _build_advanced(self) -> None:
        self._advanced_option(
            "special_option", self.special_var, "special_help")
        self._advanced_option(
            "nonwild_option", self.nonwild_var, "nonwild_help")

    def _advanced_option(
        self, label_key: str, variable: tk.BooleanVar, help_key: str
    ) -> None:
        row = ttk.Frame(self.advanced)
        row.pack(fill="x", anchor="w", pady=3)
        checkbox = ttk.Checkbutton(row, variable=variable)
        checkbox.pack(side="left", anchor="w")
        icon = add_info_icon(row, self._text(help_key))
        icon.pack(side="left", padx=(6, 0))
        self.advanced_options.append(
            (checkbox, icon.tooltip, label_key, help_key))

    def _refresh_language(self) -> None:
        self.root.title(self._text("window_title"))
        self.title_label.configure(text=self._text("app_title"))
        self.subtitle_label.configure(text=self._text("subtitle"))
        self.base_romfs_button.configure(text=self._text("choose_base_romfs"))
        self.update_romfs_button.configure(text=self._text("choose_update_romfs"))
        self.base_romfs_path_var.set(
            str(self.base_romfs_root) if self.base_romfs_root else self._text("base_not_selected"))
        self.update_romfs_path_var.set(
            str(self.update_romfs_root) if self.update_romfs_root else self._text("update_not_selected"))
        self.family_group.configure(text=self._text("families"))
        self.family_description_label.configure(text=self._text("family_description"))
        self.select_all_families_button.configure(text=self._text("select_all_families"))
        if not self.available_family_codes:
            self.family_empty_label.configure(text=self._text("families_not_loaded"))
        for code, checkbutton in self.family_checkbuttons.items():
            checkbutton.configure(text=self._family_label(code))
        self.rank_group.configure(text=self._text("ranks"))
        self.rank_description_label.configure(text=self._text("rank_description"))
        self.select_all_ranks_button.configure(text=self._text("select_all_ranks"))
        if not self.available_rank_codes:
            self.rank_empty_label.configure(text=self._text("ranks_not_loaded"))
        for code, checkbutton in self.rank_checkbuttons.items():
            checkbutton.configure(text=RANK_CODES.get(code, f"Rank {code}"))
        self.seed_label.configure(text=self._text("seed"))
        self.random_seed_label.configure(text=self._text("random_seed"))
        self.advanced.configure(text=self._text("advanced"))
        button_key = "hide_advanced" if self.advanced_open else "show_advanced"
        self.advanced_button.configure(text=self._text(button_key))
        self.generate_button.configure(
            text=self._text("create"),
            state=(
                "normal"
                if self.dataset_available and self._selected_family_codes()
                and self._selected_rank_codes() and not self.is_building
                else "disabled"
            ),
        )
        for checkbox, tooltip, label_key, help_key in self.advanced_options:
            checkbox.configure(text=self._text(label_key))
            tooltip.text = self._text(help_key)
            tooltip.hide()
        self._refresh_status()

    def _refresh_status(self) -> None:
        self.status_var.set(
            self._text(self.status_key).format(**self.status_values))

    def _set_status(self, key: str, **values: object) -> None:
        self.status_key = key
        self.status_values = values
        self._refresh_status()

    def _toggle_advanced(self) -> None:
        self.advanced_open = not self.advanced_open
        if self.advanced_open:
            self.advanced.pack(fill="x", pady=4, before=self.generate_button)
        else:
            self.advanced.pack_forget()
        self._refresh_language()

    def _select_romfs(self, layer: str) -> None:
        title_key = "base_romfs_dialog_title" if layer == "base" else "update_romfs_dialog_title"
        selected = filedialog.askdirectory(
            parent=self.root, title=self._text(title_key))
        if not selected:
            return
        selected_root = Path(selected)
        if layer == "base":
            self.base_romfs_root = selected_root
        else:
            self.update_romfs_root = selected_root
        self._validate_romfs_selection()
        self._refresh_language()

    def _validate_romfs_selection(self) -> None:
        self.dataset_available = False
        if self.base_romfs_root is None:
            self._set_status("select_base_romfs")
            return
        if self.update_romfs_root is None:
            self._set_status("select_update_romfs")
            return
        try:
            source = RomFsSource(self.base_romfs_root, self.update_romfs_root)
            kind_catalog = parse_kind_catalog(source.read("data/Parameter/KindParam.tp"))
            family_codes = tuple(sorted({
                row["family_code"] for row in kind_catalog["species"]
                if row["family_code"] > 0
            }))
            rank_codes = tuple(sorted({
                row["rank_code"] for row in kind_catalog["species"]
                if row["rank_code"] in RANK_CODES
            }))
            if not family_codes or not rank_codes:
                raise GlobalCatalogError("Nessuna famiglia o grado trovato in KindParam.tp")
        except (RomFsSourceError, GlobalCatalogError, OSError) as exc:
            self._set_status("data_error")
            self._render_family_options(())
            self._render_rank_options(())
            messagebox.showerror(self._text("data_error_title"), str(exc))
            return
        self.base_romfs_root = source.base_root
        self.update_romfs_root = source.update_root
        self._render_family_options(family_codes)
        self._render_rank_options(rank_codes)
        self.dataset_archive_count = source.describe()["et_archive_count"]
        self.dataset_available = True
        self._set_status("ready", count=self.dataset_archive_count)

    def _start_build(self) -> None:
        if not self.dataset_available:
            self._set_status("select_romfs")
            self._refresh_language()
            return
        if not self._selected_family_codes():
            messagebox.showerror(
                self._text("family_error_title"), self._text("no_family_selected"))
            return
        if not self._selected_rank_codes():
            messagebox.showerror(
                self._text("rank_error_title"), self._text("no_rank_selected"))
            return
        try:
            seed = int(self.seed_var.get().strip(), 10)
            if not 0 <= seed < 2**64:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                self._text("invalid_title"), self._text("invalid_seed"))
            return

        self.is_building = True
        self._set_status("building")
        self._refresh_language()
        worker = threading.Thread(
            target=self._build_worker,
            args=(
                seed, self.special_var.get(), self.nonwild_var.get(),
                self.base_romfs_root, self.update_romfs_root,
                self._donor_family_codes(), self._donor_rank_codes(),
            ),
            daemon=True,
        )
        worker.start()

    def _build_worker(
        self, seed: int, special: bool, nonwild: bool,
        base_romfs_root: Path | None, update_romfs_root: Path | None,
        donor_family_codes: frozenset[int] | None,
        donor_rank_codes: frozenset[int] | None,
    ) -> None:
        if base_romfs_root is None or update_romfs_root is None:
            self.root.after(0, lambda: self._finish_error(self._text("select_romfs")))
            return
        try:
            result = build_global_overlay(
                project_root=self.project,
                base_romfs_root=base_romfs_root,
                update_romfs_root=update_romfs_root,
                seed=seed,
                include_special_donors=special,
                include_nonwild_instances=nonwild,
                donor_family_codes=donor_family_codes,
                donor_rank_codes=donor_rank_codes,
            )
        except (GlobalBuildError, OSError, ValueError) as exc:
            message = str(exc)
            self.root.after(0, lambda text=message: self._finish_error(text))
            return
        self.root.after(0, lambda: self._finish_success(result))

    def _finish_error(self, message: str) -> None:
        self.is_building = False
        self._set_status("build_error")
        self._refresh_language()
        messagebox.showerror(self._text("error_title"), message)

    def _finish_success(self, result: dict) -> None:
        self.is_building = False
        zip_path = result["zip_path"]
        seed = result["manifest"]["seed"]
        self._set_status("created", seed=seed, path=zip_path)
        self._refresh_language()
        messagebox.showinfo(
            self._text("complete_title"),
            self._text("complete_message").format(path=zip_path, seed=seed),
        )


def main() -> None:
    app = GlobalRandomizerApp()
    app.root.mainloop()


if __name__ == "__main__":
    main()
