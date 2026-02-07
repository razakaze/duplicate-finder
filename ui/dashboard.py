"""Dashboard — visual summary with colored result cards and action buttons."""

import customtkinter as ctk
from typing import Callable, Optional

from models import ScanResult
from utils.formatting import format_size, format_duration
from config import (
    COLOR_SURFACE, COLOR_GREEN, COLOR_GREEN_BG, COLOR_ORANGE, COLOR_ORANGE_BG,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_TERTIARY, COLOR_BORDER,
    LABEL_FILTER_IDENTICAL, LABEL_FILTER_MODIFIED,
)


class DirectoryStatCard(ctk.CTkFrame):
    """Compact card showing one directory's stats."""

    def __init__(self, parent, label: str):
        super().__init__(parent, fg_color=COLOR_SURFACE, corner_radius=10)

        self._title = ctk.CTkLabel(
            self, text=label,
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self._title.pack(padx=15, pady=(12, 2), anchor="w")

        self._value = ctk.CTkLabel(
            self, text="--",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        self._value.pack(padx=15, pady=(0, 2), anchor="w")

        self._sub = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_TERTIARY,
        )
        self._sub.pack(padx=15, pady=(0, 12), anchor="w")

    def set_value(self, value: str, subtitle: str = ""):
        self._value.configure(text=value)
        self._sub.configure(text=subtitle)

    def set_title(self, text: str):
        self._title.configure(text=text)


class ResultCard(ctk.CTkFrame):
    """Larger card with colored accent border, description, and action button."""

    def __init__(
        self,
        parent,
        title: str,
        accent_color: str,
        bg_tint: str,
        button_text: str,
        on_action: Optional[Callable] = None,
    ):
        super().__init__(parent, fg_color=bg_tint, corner_radius=10)

        # Colored accent bar on the left
        ctk.CTkFrame(
            self, width=4, fg_color=accent_color, corner_radius=0
        ).pack(side="left", fill="y")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=15, pady=12)

        # Badge
        badge_frame = ctk.CTkFrame(content, fg_color=accent_color, corner_radius=4)
        ctk.CTkLabel(
            badge_frame,
            text=title.upper(),
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="white",
        ).pack(padx=6, pady=2)
        badge_frame.pack(anchor="w", pady=(0, 6))

        # Value
        self._value = ctk.CTkLabel(
            content, text="--",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        self._value.pack(anchor="w")

        # Subtitle
        self._sub = ctk.CTkLabel(
            content, text="",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self._sub.pack(anchor="w", pady=(2, 4))

        # Description
        self._desc = ctk.CTkLabel(
            content, text="",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_TERTIARY,
            wraplength=300,
            justify="left",
        )
        self._desc.pack(anchor="w", pady=(0, 8))

        # Action button
        self._action_btn = ctk.CTkButton(
            content,
            text=button_text,
            fg_color=accent_color,
            width=200,
            height=32,
            command=on_action,
        )
        self._action_btn.pack(anchor="w")

    def set_value(self, value: str, subtitle: str = "", description: str = ""):
        self._value.configure(text=value)
        self._sub.configure(text=subtitle)
        self._desc.configure(text=description)


class ReclaimCard(ctk.CTkFrame):
    """Full-width card showing reclaimable space."""

    def __init__(self, parent):
        super().__init__(parent, fg_color=COLOR_SURFACE, corner_radius=10)

        self._title = ctk.CTkLabel(
            self, text="Space You Can Reclaim",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self._title.pack(padx=15, pady=(12, 2), anchor="w")

        self._value = ctk.CTkLabel(
            self, text="--",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        self._value.pack(padx=15, pady=(0, 2), anchor="w")

        self._sub = ctk.CTkLabel(
            self, text="by removing extra identical copies",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_TERTIARY,
        )
        self._sub.pack(padx=15, pady=(0, 12), anchor="w")

    def set_value(self, value: str, subtitle: str = ""):
        self._value.configure(text=value)
        if subtitle:
            self._sub.configure(text=subtitle)


class Dashboard(ctk.CTkFrame):
    """Dashboard with scan summary, directory cards, result cards, and reclaim card."""

    def __init__(self, parent, on_navigate_details: Optional[Callable[[str], None]] = None):
        super().__init__(parent, fg_color="transparent")
        self._on_navigate = on_navigate_details
        self._build_ui()

    def _build_ui(self):
        # Scan summary line
        self._summary_label = ctk.CTkLabel(
            self,
            text="Run a scan to see results here.",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self._summary_label.pack(anchor="w", padx=5, pady=(5, 15))

        # Directory cards row
        dir_frame = ctk.CTkFrame(self, fg_color="transparent")
        dir_frame.pack(fill="x", pady=(0, 12))

        self._dir_cards: list[DirectoryStatCard] = []
        for i in range(3):
            card = DirectoryStatCard(dir_frame, label=f"Directory {chr(65 + i)}")
            card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 5, 0))
            self._dir_cards.append(card)

        # Result cards row
        results_frame = ctk.CTkFrame(self, fg_color="transparent")
        results_frame.pack(fill="x", pady=(0, 12))

        self._identical_card = ResultCard(
            results_frame,
            title="Identical Copies",
            accent_color=COLOR_GREEN,
            bg_tint=COLOR_GREEN_BG,
            button_text="Review Identical Copies",
            on_action=lambda: self._navigate(LABEL_FILTER_IDENTICAL),
        )
        self._identical_card.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self._modified_card = ResultCard(
            results_frame,
            title="Modified Versions",
            accent_color=COLOR_ORANGE,
            bg_tint=COLOR_ORANGE_BG,
            button_text="Review Modified Versions",
            on_action=lambda: self._navigate(LABEL_FILTER_MODIFIED),
        )
        self._modified_card.pack(side="left", fill="both", expand=True, padx=(5, 0))

        # Reclaimable space card
        self._reclaim_card = ReclaimCard(self)
        self._reclaim_card.pack(fill="x", pady=(0, 10))

    def _navigate(self, filter_value: str):
        if self._on_navigate:
            self._on_navigate(filter_value)

    def update_results(self, result: ScanResult):
        """Update all cards with scan results."""
        files_per_dir = result.files_per_directory
        dirs = result.directories

        # Summary line
        total_dur = result.scan_duration + result.hash_duration
        self._summary_label.configure(
            text=(
                f"Scanned {len(dirs)} directories \u2014 "
                f"{result.total_files:,} files \u2014 "
                f"completed in {format_duration(total_dur)}"
            ),
            text_color=COLOR_TEXT_PRIMARY,
        )

        # Directory cards
        for i, card in enumerate(self._dir_cards):
            if i < len(dirs):
                d = dirs[i]
                count = files_per_dir.get(d, 0)
                total_size = result.total_size_per_directory.get(d, 0)
                card.set_title(f"Directory {chr(65 + i)}: {d.name}")
                card.set_value(
                    f"{count:,} files",
                    subtitle=format_size(total_size),
                )
            else:
                card.set_value("--", subtitle="Not selected")

        # Identical copies
        dup_groups = len(result.binary_duplicates)
        dup_files = result.total_binary_duplicate_count
        self._identical_card.set_value(
            f"{dup_files:,} duplicate files",
            subtitle=f"in {dup_groups:,} groups",
            description="Safe to clean up \u2014 keep one copy, remove the rest.",
        )

        # Modified versions
        div_groups = len(result.diverged_files)
        div_files = sum(len(g.files) for g in result.diverged_files)
        self._modified_card.set_value(
            f"{div_files:,} files",
            subtitle=f"in {div_groups:,} groups",
            description="Same name, different content \u2014 review before acting.",
        )

        # Reclaimable space
        self._reclaim_card.set_value(
            format_size(result.total_reclaimable_bytes),
            subtitle="by removing extra identical copies",
        )
