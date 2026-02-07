"""Custom confirmation dialog for file deletion."""

import customtkinter as ctk

from models import FileRecord
from utils.formatting import format_size
from config import (
    COLOR_SURFACE, COLOR_RED, COLOR_RED_HOVER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_TERTIARY,
)


class ConfirmDeleteDialog(ctk.CTkToplevel):
    """Modal dialog confirming file deletion to the Recycle Bin."""

    def __init__(self, parent, files: list[FileRecord]):
        super().__init__(parent)
        self.title("Confirm Deletion")
        self.geometry("520x420")
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)

        self.result = False

        total_bytes = sum(f.size for f in files)
        plural = "s" if len(files) != 1 else ""

        # Header
        ctk.CTkLabel(
            self,
            text=f"Move {len(files)} file{plural} to Recycle Bin?",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(padx=20, pady=(20, 10))

        # File list
        file_list = ctk.CTkScrollableFrame(
            self, fg_color=COLOR_SURFACE, corner_radius=8, height=200
        )
        file_list.pack(fill="x", padx=20, pady=5)

        for f in files:
            rel = f"{f.directory_root.name} / {f.relative_path}"
            ctk.CTkLabel(
                file_list,
                text=rel,
                font=ctk.CTkFont(size=11),
                text_color=COLOR_TEXT_SECONDARY,
                anchor="w",
            ).pack(fill="x", padx=10, pady=1)

        # Total size
        ctk.CTkLabel(
            self,
            text=f"Total: {format_size(total_bytes)}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(padx=20, pady=5)

        # Safety message
        ctk.CTkLabel(
            self,
            text="Files are moved to the Recycle Bin and can be restored if needed.",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_TERTIARY,
        ).pack(padx=20, pady=5)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="gray40",
            width=140,
            height=36,
            command=self._cancel,
        ).pack(side="left", expand=True, padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Move to Recycle Bin",
            fg_color=COLOR_RED,
            hover_color=COLOR_RED_HOVER,
            width=200,
            height=36,
            command=self._confirm,
        ).pack(side="right", expand=True, padx=5)

        # Center the dialog on the parent window
        self.update_idletasks()
        if parent.winfo_exists():
            x = parent.winfo_rootx() + (parent.winfo_width() - 520) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - 420) // 2
            self.geometry(f"+{x}+{y}")

    def _confirm(self):
        self.result = True
        self.destroy()

    def _cancel(self):
        self.result = False
        self.destroy()
