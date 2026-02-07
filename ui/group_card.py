"""Card widget representing one duplicate group with file rows."""

from pathlib import Path
import customtkinter as ctk

from models import DuplicateGroup, MatchType, FileRecord
from utils.formatting import format_size
from config import (
    COLOR_GREEN, COLOR_GREEN_BG, COLOR_ORANGE, COLOR_ORANGE_BG,
    COLOR_BORDER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_TERTIARY,
    COLOR_PRIMARY, COLOR_SURFACE_HOVER, COLOR_SURFACE,
    LABEL_IDENTICAL, LABEL_MODIFIED,
)
from ui.file_row import FileRow


class DuplicateGroupCard(ctk.CTkFrame):
    """A card for one duplicate group, containing FileRow widgets."""

    def __init__(self, parent, group: DuplicateGroup, on_selection_change):
        is_identical = group.match_type == MatchType.BINARY_DUPLICATE
        accent = COLOR_GREEN if is_identical else COLOR_ORANGE
        bg_tint = COLOR_GREEN_BG if is_identical else COLOR_ORANGE_BG
        badge_text = LABEL_IDENTICAL.upper() if is_identical else LABEL_MODIFIED.upper()

        super().__init__(
            parent,
            fg_color=bg_tint,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDER,
        )

        self._group = group
        self._on_selection_change = on_selection_change

        # Colored accent bar on the left
        accent_bar = ctk.CTkFrame(self, width=4, fg_color=accent, corner_radius=0)
        accent_bar.pack(side="left", fill="y")

        # Content area
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        # --- Header row ---
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))

        # Badge
        badge_frame = ctk.CTkFrame(header, fg_color=accent, corner_radius=4)
        ctk.CTkLabel(
            badge_frame,
            text=badge_text,
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="white",
        ).pack(padx=6, pady=2)
        badge_frame.pack(side="left", padx=(0, 10))

        # Group name and count
        copies_text = f'"{group.shared_name}" \u2014 {len(group.files)} copies'
        if is_identical and group.files:
            copies_text += f" \u2014 {format_size(group.files[0].size)} each"

        ctk.CTkLabel(
            header,
            text=copies_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(side="left")

        # Selection count indicator
        self._sel_count_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_TERTIARY,
        )
        self._sel_count_label.pack(side="right")

        # --- File rows (sorted newest first) ---
        recommended = group.newest_file
        sorted_files = sorted(group.files, key=lambda f: f.modified, reverse=True)

        self._file_rows: list[FileRow] = []
        for file_rec in sorted_files:
            is_keep = is_identical and (file_rec is recommended)
            row = FileRow(
                content,
                file_rec,
                is_recommended_keep=is_keep,
                on_check_change=self._on_any_check_change,
            )
            row.pack(fill="x", pady=2)
            self._file_rows.append(row)

        # --- Bottom area ---
        bottom = ctk.CTkFrame(content, fg_color="transparent")
        bottom.pack(fill="x", pady=(8, 0))

        if is_identical:
            ctk.CTkButton(
                bottom,
                text="Select all except newest",
                fg_color="transparent",
                text_color=COLOR_PRIMARY,
                hover_color=COLOR_SURFACE_HOVER,
                border_width=1,
                border_color=COLOR_PRIMARY,
                height=28,
                command=self.select_all_except_keep,
            ).pack(side="left")
        else:
            ctk.CTkLabel(
                bottom,
                text=(
                    "These files have the same name but different content. "
                    "Review each version before deciding which to keep."
                ),
                font=ctk.CTkFont(size=10),
                text_color=COLOR_TEXT_TERTIARY,
                wraplength=500,
                justify="left",
            ).pack(side="left")

    def _on_any_check_change(self):
        """Called when any checkbox in this card is toggled."""
        count = sum(1 for r in self._file_rows if r.is_checked)
        total = len(self._file_rows)
        if count > 0:
            self._sel_count_label.configure(text=f"{count} of {total} selected")
        else:
            self._sel_count_label.configure(text="")
        self._on_selection_change()

    def select_all_except_keep(self):
        """Check all files except the recommended-keep (newest) one."""
        recommended = self._group.newest_file
        for row in self._file_rows:
            row.set_checked(row.file_record is not recommended)
        self._on_any_check_change()

    def deselect_all(self):
        """Uncheck all checkboxes."""
        for row in self._file_rows:
            row.set_checked(False)
        self._on_any_check_change()

    def select_from_directory(self, directory: Path):
        """Check all files originating from the given directory."""
        for row in self._file_rows:
            if row.file_record.directory_root == directory:
                row.set_checked(True)
        self._on_any_check_change()

    def get_selected_files(self) -> list[FileRecord]:
        """Return list of checked files."""
        return [r.file_record for r in self._file_rows if r.is_checked]

    def remove_file_row(self, file_record: FileRecord):
        """Remove a specific file row (after deletion)."""
        for row in self._file_rows:
            if row.file_record is file_record:
                row.pack_forget()
                row.destroy()
                self._file_rows.remove(row)
                break
        self._on_any_check_change()

    @property
    def remaining_file_count(self) -> int:
        return len(self._file_rows)
