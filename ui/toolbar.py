"""Toolbar — filter, export buttons, batch directory select, and status."""

from pathlib import Path
import customtkinter as ctk
from typing import Callable, Optional

from config import (
    LABEL_FILTER_ALL, LABEL_FILTER_IDENTICAL, LABEL_FILTER_MODIFIED,
    COLOR_TEXT_TERTIARY,
)


class Toolbar(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        on_export_csv: Optional[Callable] = None,
        on_export_json: Optional[Callable] = None,
        on_filter_change: Optional[Callable[[str], None]] = None,
        on_dir_select: Optional[Callable[[Path], None]] = None,
    ):
        super().__init__(parent)
        self._on_filter_change = on_filter_change
        self._on_dir_select = on_dir_select
        self._directories: list[Path] = []
        self._build_ui(on_export_csv, on_export_json)

    def _build_ui(self, on_export_csv, on_export_json):
        # Filter
        ctk.CTkLabel(self, text="Filter:").pack(side="left", padx=(5, 5))

        self._filter_var = ctk.StringVar(value=LABEL_FILTER_ALL)
        self._filter_menu = ctk.CTkOptionMenu(
            self,
            variable=self._filter_var,
            values=[LABEL_FILTER_ALL, LABEL_FILTER_IDENTICAL, LABEL_FILTER_MODIFIED],
            command=self._on_filter_selected,
            width=160,
        )
        self._filter_menu.pack(side="left", padx=(0, 15))

        # Batch directory select
        ctk.CTkLabel(self, text="Select all from:").pack(side="left", padx=(0, 5))

        self._dir_select_var = ctk.StringVar(value="--")
        self._dir_select_menu = ctk.CTkOptionMenu(
            self,
            variable=self._dir_select_var,
            values=["--"],
            command=self._on_dir_selected,
            width=180,
        )
        self._dir_select_menu.pack(side="left", padx=(0, 15))

        # Export buttons
        ctk.CTkButton(
            self, text="Export CSV", width=100, command=on_export_csv
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            self, text="Export JSON", width=100, command=on_export_json
        ).pack(side="left", padx=(0, 10))

        # Status label
        self._status_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_TERTIARY
        )
        self._status_label.pack(side="right", padx=5)

    def _on_filter_selected(self, value: str):
        if self._on_filter_change:
            self._on_filter_change(value)

    def _on_dir_selected(self, value: str):
        if value == "--" or not self._on_dir_select:
            return
        for d in self._directories:
            if d.name == value:
                self._on_dir_select(d)
                # Reset dropdown to "--" after selection
                self._dir_select_var.set("--")
                break

    def set_directories(self, directories: list[Path]):
        """Populate the directory batch-select dropdown."""
        self._directories = directories
        names = [d.name for d in directories]
        self._dir_select_menu.configure(values=["--"] + names)

    def set_filter(self, value: str):
        """Programmatically set the filter (used by Dashboard action buttons)."""
        self._filter_var.set(value)
        if self._on_filter_change:
            self._on_filter_change(value)

    def set_status(self, text: str):
        self._status_label.configure(text=text)
