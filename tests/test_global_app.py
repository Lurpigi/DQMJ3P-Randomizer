from __future__ import annotations

import sys
import tkinter as tk
import unittest
from pathlib import Path
from tkinter import ttk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dqmj3p_randomizer.global_app import GlobalRandomizerApp


class InfoTooltipTests(unittest.TestCase):
    def test_hover_focus_escape_and_destroy_show_a_mapped_readable_tooltip(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk non disponibile: {exc}")
        def destroy_root() -> None:
            try:
                root.destroy()
            except tk.TclError:
                pass
        self.addCleanup(destroy_root)
        try:
            root.attributes("-alpha", 0)
        except tk.TclError:
            pass
        root.geometry("720x520+0+0")
        app = GlobalRandomizerApp(root)
        app._toggle_advanced()
        root.update()

        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)

        icons = [
            widget for widget in descendants(app.advanced)
            if isinstance(widget, ttk.Label) and widget.cget("text") == "ⓘ"
        ]
        self.assertEqual(len(icons), 2)
        icon = icons[0]
        self.assertEqual(str(icon.cget("takefocus")), "1")

        icon.event_generate("<Enter>")
        root.update()
        tip = icon.tooltip.tip
        self.assertIsNotNone(tip)
        self.assertTrue(tip.winfo_ismapped())
        self.assertTrue(tip.winfo_viewable())
        label = tip.winfo_children()[0]
        self.assertEqual(label.cget("background"), "#ffffe0")
        self.assertEqual(label.cget("foreground"), "black")

        icon.event_generate("<Leave>")
        root.update()
        self.assertIsNone(icon.tooltip.tip)

        icon.focus_force()
        icon.event_generate("<FocusIn>")
        root.update()
        self.assertIsNotNone(icon.tooltip.tip)
        self.assertTrue(icon.tooltip.tip.winfo_ismapped())
        icon.event_generate("<KeyPress-Escape>", when="now")
        root.update()
        self.assertIsNone(icon.tooltip.tip)
        root.destroy()
        self.assertIsNone(icon.tooltip.tip)


if __name__ == "__main__":
    unittest.main()
