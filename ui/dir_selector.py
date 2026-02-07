"""Directory selection panel — up to 3 input directories + 1 output directory."""

import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path
from typing import Optional


class DirectorySelector(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self._dir_entries: list[ctk.CTkEntry] = []
        self._dir_paths: list[Optional[Path]] = [None, None, None]
        self._output_path: Optional[Path] = None

        self._build_ui()

    def _build_ui(self):
        title = ctk.CTkLabel(
            self,
            text="Input Directories (select 2 or 3):",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        title.pack(anchor="w", padx=5, pady=(5, 10))

        labels = ["Directory A (required):", "Directory B (required):", "Directory C (optional):"]
        for i, label_text in enumerate(labels):
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=2)

            label = ctk.CTkLabel(row, text=label_text, width=180, anchor="w")
            label.pack(side="left")

            entry = ctk.CTkEntry(row, placeholder_text="Select a directory...")
            entry.pack(side="left", fill="x", expand=True, padx=(5, 5))
            self._dir_entries.append(entry)

            browse_btn = ctk.CTkButton(
                row,
                text="Browse",
                width=80,
                command=lambda idx=i: self._browse_dir(idx),
            )
            browse_btn.pack(side="left", padx=(0, 5))

            clear_btn = ctk.CTkButton(
                row,
                text="Clear",
                width=60,
                fg_color="gray40",
                command=lambda idx=i: self._clear_dir(idx),
            )
            clear_btn.pack(side="left")

        # Output directory
        sep = ctk.CTkLabel(
            self,
            text="Output Directory (for reports):",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        sep.pack(anchor="w", padx=5, pady=(15, 5))

        out_row = ctk.CTkFrame(self, fg_color="transparent")
        out_row.pack(fill="x", padx=5, pady=2)

        out_label = ctk.CTkLabel(out_row, text="Report output:", width=180, anchor="w")
        out_label.pack(side="left")

        self._output_entry = ctk.CTkEntry(
            out_row, placeholder_text="Select output directory..."
        )
        self._output_entry.pack(side="left", fill="x", expand=True, padx=(5, 5))

        out_browse = ctk.CTkButton(
            out_row,
            text="Browse",
            width=80,
            command=self._browse_output,
        )
        out_browse.pack(side="left")

    def _browse_dir(self, index: int):
        path = filedialog.askdirectory(title=f"Select Directory {chr(65 + index)}")
        if path:
            p = Path(path)
            self._dir_paths[index] = p
            entry = self._dir_entries[index]
            entry.delete(0, "end")
            entry.insert(0, str(p))

    def _clear_dir(self, index: int):
        self._dir_paths[index] = None
        entry = self._dir_entries[index]
        entry.delete(0, "end")

    def _browse_output(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self._output_path = Path(path)
            self._output_entry.delete(0, "end")
            self._output_entry.insert(0, str(self._output_path))

    def get_directories(self) -> list[Path]:
        """Return list of valid, selected input directories."""
        result = []
        for i, entry in enumerate(self._dir_entries):
            text = entry.get().strip()
            if text:
                p = Path(text)
                if p.is_dir():
                    self._dir_paths[i] = p
                    result.append(p)
        return result

    def get_output_directory(self) -> Optional[Path]:
        """Return the output directory, or None if not set."""
        text = self._output_entry.get().strip()
        if text:
            p = Path(text)
            if p.is_dir():
                return p
        return None
