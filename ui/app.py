"""Main application window with tab navigation, scan orchestration, and wiring."""

import time
import customtkinter as ctk
from pathlib import Path
from typing import Optional

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT,
    LABEL_FILTER_IDENTICAL, LABEL_FILTER_MODIFIED,
)
from models import ScanResult
from scanner import scan_directory
from analyzer import find_duplicates
from utils.threading_utils import BackgroundTask
from ui.dir_selector import DirectorySelector
from ui.scan_progress import ScanProgress
from ui.dashboard import Dashboard
from ui.file_list import FileListView
from ui.toolbar import Toolbar

# How often the UI polls the shared progress state (milliseconds)
_POLL_INTERVAL_MS = 200


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.scan_result: Optional[ScanResult] = None
        self._current_task: Optional[BackgroundTask] = None

        # Shared progress state — written by background thread, read by UI poll
        self._progress_phase: str = ""
        self._progress_status: str = ""
        self._progress_fraction: float = 0.0
        self._progress_indeterminate: bool = False
        self._progress_dir_counts: list[tuple[int, int, str]] = []  # (index, count, name)

        self._build_ui()

    def _build_ui(self):
        # Tab navigation
        self.tab_view = ctk.CTkTabview(self, anchor="nw")
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        self.tab_setup = self.tab_view.add("Setup")
        self.tab_dashboard = self.tab_view.add("Dashboard")
        self.tab_details = self.tab_view.add("Details")

        # --- Setup tab ---
        self.dir_selector = DirectorySelector(self.tab_setup)
        self.dir_selector.pack(fill="x", padx=10, pady=10)

        self.scan_progress = ScanProgress(self.tab_setup)
        self.scan_progress.pack(fill="x", padx=10, pady=(0, 10))

        # Buttons: Start + Cancel
        self._btn_frame = ctk.CTkFrame(self.tab_setup, fg_color="transparent")
        self._btn_frame.pack(padx=10, pady=10)

        self.btn_scan = ctk.CTkButton(
            self._btn_frame,
            text="Start Scan",
            command=self._start_scan,
            height=40,
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.btn_scan.pack(side="left", padx=(0, 10))

        self.btn_cancel = ctk.CTkButton(
            self._btn_frame,
            text="Cancel",
            command=self._cancel_scan,
            height=40,
            fg_color="gray40",
            hover_color="gray50",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        # Cancel button starts hidden — only shown during scanning

        # --- Dashboard tab ---
        self.dashboard = Dashboard(
            self.tab_dashboard,
            on_navigate_details=self._navigate_to_details_filtered,
        )
        self.dashboard.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Details tab ---
        self.toolbar = Toolbar(
            self.tab_details,
            on_export_csv=self._export_csv,
            on_export_json=self._export_json,
            on_filter_change=self._apply_filter,
            on_dir_select=self._select_all_from_dir,
        )
        self.toolbar.pack(fill="x", padx=10, pady=(10, 5))

        self.file_list = FileListView(self.tab_details)
        self.file_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ---- UI poll loop ----

    def _start_progress_poll(self):
        """Start a repeating timer that reads shared state and updates the UI."""
        self._poll_progress()

    def _poll_progress(self):
        """Read shared progress state and update widgets. Reschedule self."""
        if self._current_task is None:
            return  # No scan running, stop polling

        # Update UI from shared state
        self.scan_progress.set_phase(self._progress_phase)
        self.scan_progress.set_status(self._progress_status)

        if self._progress_indeterminate:
            self.scan_progress.set_indeterminate(True)
        else:
            self.scan_progress.set_indeterminate(False)
            self.scan_progress.set_progress(self._progress_fraction)

        for idx, count, name in self._progress_dir_counts:
            self.scan_progress.set_dir_count(idx, count, name)

        # Keep polling while the task is running
        if not self._current_task.is_finished:
            self.after(_POLL_INTERVAL_MS, self._poll_progress)

    # ---- Scan control ----

    def _start_scan(self):
        directories = self.dir_selector.get_directories()
        if len(directories) < 2:
            self.scan_progress.set_status("Select at least 2 directories to scan.")
            return

        # Show cancel, hide start
        self.btn_scan.pack_forget()
        self.btn_cancel.pack(side="left")
        self.scan_progress.reset()

        # Reset shared state
        self._progress_phase = ""
        self._progress_status = ""
        self._progress_fraction = 0.0
        self._progress_indeterminate = False
        self._progress_dir_counts = []

        def scan_task(cancelled):
            """Runs entirely in the background thread. No after() calls."""
            all_files = []
            scan_start = time.time()

            # Phase 1: Metadata scan
            self._progress_phase = "Phase 1 of 2: Scanning files..."
            self._progress_indeterminate = True

            for i, directory in enumerate(directories):
                if cancelled():
                    return None
                self._progress_status = f"Scanning {directory.name}..."

                def dir_progress(count, _i=i, _dir=directory):
                    self._progress_dir_counts = [
                        (idx, c, n) if idx != _i else (_i, count, _dir.name)
                        for idx, c, n in self._progress_dir_counts
                    ]
                    # Add entry if not yet present
                    if not any(idx == _i for idx, _, _ in self._progress_dir_counts):
                        self._progress_dir_counts.append((_i, count, _dir.name))

                files = scan_directory(
                    directory,
                    progress_callback=dir_progress,
                    cancelled=cancelled,
                )
                all_files.extend(files)

            scan_duration = time.time() - scan_start

            if cancelled():
                return None

            # Phase 2: Hash & classify
            self._progress_indeterminate = False
            self._progress_fraction = 0.0
            self._progress_phase = "Phase 2 of 2: Comparing files..."
            self._progress_status = (
                f"{len(all_files):,} files found. Comparing candidates..."
            )

            hash_start = time.time()

            def hash_progress(current, total):
                self._progress_fraction = current / total if total > 0 else 0
                self._progress_status = (
                    f"Comparing file {current:,} of {total:,}..."
                )

            binary_dups, diverged = find_duplicates(
                all_files,
                progress_callback=hash_progress,
                cancelled=cancelled,
            )
            hash_duration = time.time() - hash_start

            # Pre-compute summary stats while still on background thread
            # so we can drop all_files and free ~12k non-duplicate records
            file_count = len(all_files)
            count_per_dir: dict[Path, int] = {}
            size_per_dir: dict[Path, int] = {}
            for f in all_files:
                count_per_dir[f.directory_root] = count_per_dir.get(f.directory_root, 0) + 1
                size_per_dir[f.directory_root] = size_per_dir.get(f.directory_root, 0) + f.size

            # all_files is NOT passed to ScanResult — it gets garbage-collected
            return ScanResult(
                directories=directories,
                binary_duplicates=binary_dups,
                diverged_files=diverged,
                scan_duration=scan_duration,
                hash_duration=hash_duration,
                total_files=file_count,
                files_per_directory=count_per_dir,
                total_size_per_directory=size_per_dir,
            )

        self._current_task = BackgroundTask(
            self,
            task_fn=scan_task,
            on_complete=self._on_scan_complete,
            on_error=self._on_scan_error,
        )
        self._current_task.start()
        self._start_progress_poll()

    def _cancel_scan(self):
        if self._current_task:
            self._current_task.cancel()
            self._current_task = None
        self._restore_scan_buttons()
        self.scan_progress.set_indeterminate(False)
        self.scan_progress.set_status("Scan cancelled.")

    def _restore_scan_buttons(self):
        """Hide cancel, show start."""
        self.btn_cancel.pack_forget()
        self.btn_scan.pack(side="left", padx=(0, 10))

    def _on_scan_complete(self, result: Optional[ScanResult]):
        self._current_task = None
        self._restore_scan_buttons()
        if result is None:
            self.scan_progress.set_status("Scan cancelled.")
            return

        self.scan_result = result

        # Step 1 (immediate): update progress indicators
        self.scan_progress.set_indeterminate(False)
        self.scan_progress.set_progress(1.0)
        self.scan_progress.set_phase("")
        self.scan_progress.set_status(
            f"Done! {result.total_files:,} files scanned. "
            f"{len(result.binary_duplicates)} identical-copy groups, "
            f"{len(result.diverged_files)} modified-version groups."
        )

        # Step 2 (after UI breathes): update dashboard + switch tab
        self.after(50, self._finish_scan_step2, result)

    def _finish_scan_step2(self, result: ScanResult):
        """Update dashboard (lightweight label updates) and switch tab."""
        self.dashboard.update_results(result)
        self.tab_view.set("Dashboard")

        # Step 3 (after UI breathes): kick off batched file list + toolbar
        self.after(100, self._finish_scan_step3, result)

    def _finish_scan_step3(self, result: ScanResult):
        """Start batched card loading in Details tab (runs in background via after batches)."""
        self.file_list.update_results(result)
        self.toolbar.set_directories(result.directories)

    def _on_scan_error(self, error: Exception):
        self._current_task = None
        self._restore_scan_buttons()
        self.scan_progress.set_indeterminate(False)
        self.scan_progress.set_status(f"Error: {error}")

    # ---- Navigation ----

    def _navigate_to_details_filtered(self, filter_value: str):
        """Navigate from Dashboard to Details tab with a filter pre-applied."""
        self.toolbar.set_filter(filter_value)
        self.file_list.apply_filter(filter_value)
        self.tab_view.set("Details")

    def _apply_filter(self, filter_value: str):
        self.file_list.apply_filter(filter_value)

    def _select_all_from_dir(self, directory: Path):
        self.file_list.select_all_from_directory(directory)

    # ---- Export ----

    def _export_csv(self):
        if not self.scan_result:
            return
        output_dir = self.dir_selector.get_output_directory()
        if not output_dir:
            self.toolbar.set_status("Set an output directory in Setup tab first.")
            return
        from report_writer import write_csv_report
        path = write_csv_report(self.scan_result, output_dir)
        self.toolbar.set_status(f"CSV exported: {path.name}")

    def _export_json(self):
        if not self.scan_result:
            return
        output_dir = self.dir_selector.get_output_directory()
        if not output_dir:
            self.toolbar.set_status("Set an output directory in Setup tab first.")
            return
        from report_writer import write_json_summary
        path = write_json_summary(self.scan_result, output_dir)
        self.toolbar.set_status(f"JSON exported: {path.name}")
