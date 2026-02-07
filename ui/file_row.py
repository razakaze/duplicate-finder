"""Single file entry widget with checkbox, file info, and Open button."""

import customtkinter as ctk

from models import FileRecord
from utils.formatting import format_size, format_date
from utils.platform_utils import reveal_in_file_manager
from config import (
    COLOR_SURFACE, COLOR_BORDER, COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY, COLOR_TEXT_TERTIARY,
    COLOR_KEEP_BADGE_BG, COLOR_KEEP_BADGE_TEXT,
)


class FileRow(ctk.CTkFrame):
    """A single file entry within a group card, with a checkbox."""

    def __init__(
        self,
        parent,
        file_record: FileRecord,
        is_recommended_keep: bool,
        on_check_change,
    ):
        super().__init__(
            parent,
            fg_color=COLOR_SURFACE,
            corner_radius=6,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self._file_record = file_record
        self._on_check_change = on_check_change

        # Checkbox
        self._var = ctk.BooleanVar(value=False)
        self._checkbox = ctk.CTkCheckBox(
            self,
            text="",
            variable=self._var,
            width=24,
            checkbox_width=20,
            checkbox_height=20,
            command=self._on_toggle,
        )
        self._checkbox.pack(side="left", padx=(10, 5), pady=8)

        # KEEP badge (only for recommended files in identical-copy groups)
        if is_recommended_keep:
            badge = ctk.CTkFrame(
                self, fg_color=COLOR_KEEP_BADGE_BG, corner_radius=4
            )
            ctk.CTkLabel(
                badge,
                text="KEEP",
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=COLOR_KEEP_BADGE_TEXT,
            ).pack(padx=6, pady=2)
            badge.pack(side="left", padx=(0, 8))

        # File info area
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=5, pady=8)

        # Line 1: filename
        ctk.CTkLabel(
            info,
            text=file_record.filename,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x")

        # Line 2: relative path
        rel_display = f"{file_record.directory_root.name} / {file_record.relative_path}"
        ctk.CTkLabel(
            info,
            text=rel_display,
            font=ctk.CTkFont(size=10),
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x")

        # Line 3: size + date
        meta_text = (
            f"{format_size(file_record.size)}  \u2014  "
            f"Modified: {format_date(file_record.modified)}"
        )
        ctk.CTkLabel(
            info,
            text=meta_text,
            font=ctk.CTkFont(size=10),
            text_color=COLOR_TEXT_TERTIARY,
            anchor="w",
        ).pack(fill="x")

        # Open in Explorer button
        ctk.CTkButton(
            self,
            text="Open",
            width=50,
            height=28,
            fg_color="gray40",
            command=self._open_location,
        ).pack(side="right", padx=10, pady=8)

    def _on_toggle(self):
        self._on_check_change()

    def _open_location(self):
        reveal_in_file_manager(self._file_record.path)

    @property
    def is_checked(self) -> bool:
        return self._var.get()

    def set_checked(self, value: bool):
        self._var.set(value)

    @property
    def file_record(self) -> FileRecord:
        return self._file_record
