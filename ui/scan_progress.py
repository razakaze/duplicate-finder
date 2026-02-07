"""Progress bar and status for scan operations — indeterminate + per-directory counts."""

import customtkinter as ctk

from config import COLOR_TEXT_SECONDARY, COLOR_TEXT_TERTIARY


class ScanProgress(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        # Phase label (e.g. "Phase 1 of 2: Scanning files...")
        self._phase_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        )
        self._phase_label.pack(fill="x", padx=5, pady=(5, 0))

        # Status text
        self._status_label = ctk.CTkLabel(
            self, text="Ready", anchor="w", font=ctk.CTkFont(size=12)
        )
        self._status_label.pack(fill="x", padx=5, pady=(2, 2))

        # Progress bar
        self._progress_bar = ctk.CTkProgressBar(self)
        self._progress_bar.pack(fill="x", padx=5, pady=(0, 5))
        self._progress_bar.set(0)

        # Per-directory file counts
        self._dir_count_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._dir_count_frame.pack(fill="x", padx=5, pady=(0, 5))

        self._dir_count_labels: list[ctk.CTkLabel] = []
        for i in range(3):
            lbl = ctk.CTkLabel(
                self._dir_count_frame,
                text=f"Dir {chr(65 + i)}: --",
                font=ctk.CTkFont(size=11),
                text_color=COLOR_TEXT_TERTIARY,
            )
            lbl.pack(side="left", expand=True)
            self._dir_count_labels.append(lbl)

    def set_phase(self, phase_text: str):
        """Set the phase label text."""
        self._phase_label.configure(text=phase_text)

    def set_status(self, text: str):
        """Set the status line text."""
        self._status_label.configure(text=text)

    def set_progress(self, value: float):
        """Set determinate progress bar value (0.0 to 1.0)."""
        self._progress_bar.set(max(0.0, min(1.0, value)))

    def set_indeterminate(self, on: bool):
        """Toggle indeterminate (animated) progress bar mode."""
        if on:
            self._progress_bar.configure(mode="indeterminate")
            self._progress_bar.start()
        else:
            self._progress_bar.stop()
            self._progress_bar.configure(mode="determinate")
            self._progress_bar.set(0)

    def set_dir_count(self, index: int, count: int, dir_name: str = ""):
        """Update the live file count for a directory."""
        if 0 <= index < 3:
            label = dir_name if dir_name else f"Dir {chr(65 + index)}"
            self._dir_count_labels[index].configure(
                text=f"{label}: {count:,} files"
            )

    def reset(self):
        """Reset all progress indicators."""
        self._progress_bar.stop()
        self._progress_bar.configure(mode="determinate")
        self._progress_bar.set(0)
        self._status_label.configure(text="Ready")
        self._phase_label.configure(text="")
        for lbl in self._dir_count_labels:
            lbl.configure(text="--")
