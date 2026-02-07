"""Sticky bottom bar showing selection count and delete button."""

import customtkinter as ctk

from utils.formatting import format_size
from config import (
    COLOR_SURFACE, COLOR_BORDER, COLOR_RED, COLOR_RED_HOVER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_TERTIARY,
)


class FloatingActionBar(ctk.CTkFrame):
    """Persistent bar at the bottom of the Details tab."""

    def __init__(self, parent, on_delete):
        super().__init__(
            parent,
            fg_color=COLOR_SURFACE,
            corner_radius=0,
            height=50,
            border_width=1,
            border_color=COLOR_BORDER,
        )

        self._summary_label = ctk.CTkLabel(
            self,
            text="No files selected",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_TERTIARY,
        )
        self._summary_label.pack(side="left", padx=15)

        self._delete_btn = ctk.CTkButton(
            self,
            text="Delete Selected",
            fg_color=COLOR_RED,
            hover_color=COLOR_RED_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"),
            width=160,
            height=36,
            state="disabled",
            command=on_delete,
        )
        self._delete_btn.pack(side="right", padx=15, pady=7)

    def update_selection(self, count: int, total_bytes: int):
        """Update the selection summary and enable/disable delete button."""
        if count == 0:
            self._summary_label.configure(
                text="No files selected", text_color=COLOR_TEXT_TERTIARY
            )
            self._delete_btn.configure(state="disabled")
        else:
            plural = "s" if count != 1 else ""
            self._summary_label.configure(
                text=f"{count} file{plural} selected ({format_size(total_bytes)})",
                text_color=COLOR_TEXT_PRIMARY,
            )
            self._delete_btn.configure(state="normal")
