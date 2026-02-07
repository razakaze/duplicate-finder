"""Duplicate file list using ttk.Treeview (virtualized) + detail panel.

The Treeview handles 2000+ groups without any lag because it only renders
visible rows. When the user clicks a group, a small detail panel shows
the individual files with checkboxes.
"""

from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from models import ScanResult, DuplicateGroup, MatchType, FileRecord
from utils.formatting import format_size, format_date
from utils.platform_utils import reveal_in_file_manager
from config import (
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_TERTIARY,
    COLOR_SURFACE, COLOR_BORDER,
    COLOR_GREEN, COLOR_GREEN_BG, COLOR_ORANGE, COLOR_ORANGE_BG,
    COLOR_RED, COLOR_RED_HOVER,
    COLOR_PRIMARY, COLOR_KEEP_BADGE_BG, COLOR_KEEP_BADGE_TEXT,
    LABEL_FILTER_ALL, LABEL_FILTER_IDENTICAL, LABEL_FILTER_MODIFIED,
    LABEL_IDENTICAL, LABEL_MODIFIED,
    DIR_COLORS,
)
from ui.floating_action_bar import FloatingActionBar
from ui.confirm_dialog import ConfirmDeleteDialog


class FileListView(ctk.CTkFrame):
    """Treeview-based group list + detail panel for the selected group."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._result: Optional[ScanResult] = None
        self._current_filter = LABEL_FILTER_ALL

        # All groups in current filter (data only — no widgets per group)
        self._groups: list[DuplicateGroup] = []
        # Map treeview item id → group index
        self._item_to_group: dict[str, int] = {}
        # Currently selected group index
        self._selected_group_idx: Optional[int] = None

        # Global selection state: set of (group_idx, file_idx) tuples
        self._checked: set[tuple[int, int]] = set()

        # Directory identity: maps directory_root → ("A", color, bg_color)
        self._dir_labels: dict[Path, tuple[str, str, str]] = {}

        self._build_ui()

    def _build_ui(self):
        # --- Main paned layout: group list (top) + detail panel (bottom) ---
        self._paned = ctk.CTkFrame(self, fg_color="transparent")
        self._paned.pack(fill="both", expand=True)

        # == Top: Group list with Treeview ==
        tree_frame = ctk.CTkFrame(self._paned, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True)

        # Style the treeview for dark mode
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Groups.Treeview",
            background="#2a2a40",
            foreground="#f0f0f5",
            fieldbackground="#2a2a40",
            rowheight=28,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Groups.Treeview.Heading",
            background="#333355",
            foreground="#f0f0f5",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Groups.Treeview",
            background=[("selected", "#3b5998")],
            foreground=[("selected", "#ffffff")],
        )

        columns = ("type", "filename", "copies", "size", "selected")
        self._tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="Groups.Treeview",
            selectmode="browse",
        )
        self._tree.heading("type", text="Type")
        self._tree.heading("filename", text="Filename")
        self._tree.heading("copies", text="Copies")
        self._tree.heading("size", text="Size Each")
        self._tree.heading("selected", text="Selected")

        self._tree.column("type", width=120, minwidth=80)
        self._tree.column("filename", width=300, minwidth=150)
        self._tree.column("copies", width=70, minwidth=50, anchor="center")
        self._tree.column("size", width=100, minwidth=70, anchor="e")
        self._tree.column("selected", width=80, minwidth=60, anchor="center")

        # Scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=tree_scroll.set)

        self._tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # == Bottom: Detail panel for selected group ==
        self._detail_frame = ctk.CTkFrame(self._paned, fg_color=COLOR_SURFACE, corner_radius=8, height=250)
        self._detail_frame.pack(fill="x", padx=0, pady=(5, 0))
        self._detail_frame.pack_propagate(False)

        # Detail header row: group info + directory legend
        detail_top = ctk.CTkFrame(self._detail_frame, fg_color="transparent")
        detail_top.pack(fill="x", padx=15, pady=(10, 5))

        self._detail_header = ctk.CTkLabel(
            detail_top,
            text="Select a group above to see its files",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self._detail_header.pack(side="left")

        # Directory legend (filled when results arrive)
        self._legend_frame = ctk.CTkFrame(detail_top, fg_color="transparent")
        self._legend_frame.pack(side="right")

        # Scrollable area for file rows inside detail panel
        self._detail_scroll = ctk.CTkScrollableFrame(
            self._detail_frame, fg_color="transparent", corner_radius=0
        )
        self._detail_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        # Action buttons row inside detail panel
        self._detail_actions = ctk.CTkFrame(self._detail_frame, fg_color="transparent")
        self._detail_actions.pack(fill="x", padx=10, pady=(0, 8))

        self._btn_select_except = ctk.CTkButton(
            self._detail_actions,
            text="Select all except newest",
            fg_color="transparent",
            text_color=COLOR_PRIMARY,
            hover_color="#2a2a4a",
            border_width=1,
            border_color=COLOR_PRIMARY,
            height=28,
            width=200,
            command=self._select_all_except_newest,
        )

        self._btn_deselect = ctk.CTkButton(
            self._detail_actions,
            text="Deselect all",
            fg_color="transparent",
            text_color=COLOR_TEXT_SECONDARY,
            hover_color="#2a2a4a",
            border_width=1,
            border_color=COLOR_BORDER,
            height=28,
            width=120,
            command=self._deselect_group,
        )

        # Floating action bar at the very bottom
        self._floating_bar = FloatingActionBar(self, on_delete=self.delete_selected)
        self._floating_bar.pack(fill="x", side="bottom")

        # Detail file row widgets (re-created when group changes)
        self._file_row_widgets: list[ctk.CTkFrame] = []
        self._file_check_vars: list[tk.BooleanVar] = []

    def _build_legend(self):
        """Build the directory legend showing A=..., B=..., C=..."""
        for w in self._legend_frame.winfo_children():
            w.destroy()

        if not self._result:
            return

        for d in self._result.directories:
            info = self._dir_labels.get(d)
            if not info:
                continue
            letter, fg, _bg = info

            item = ctk.CTkFrame(self._legend_frame, fg_color="transparent")
            item.pack(side="left", padx=(10, 0))

            badge = ctk.CTkFrame(item, fg_color=fg, corner_radius=3, width=22, height=22)
            badge.pack(side="left", padx=(0, 4))
            badge.pack_propagate(False)
            ctk.CTkLabel(
                badge, text=letter,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="white",
            ).pack(expand=True)

            ctk.CTkLabel(
                item, text=d.name,
                font=ctk.CTkFont(size=10),
                text_color=COLOR_TEXT_SECONDARY,
            ).pack(side="left")

    # ---- Data loading ----

    def update_results(self, result: ScanResult):
        """Load new scan results."""
        self._result = result
        self._checked.clear()
        self._selected_group_idx = None

        # Build directory → label mapping ("A"/"B"/"C" with colors)
        self._dir_labels.clear()
        for i, d in enumerate(result.directories):
            letter = chr(65 + i)  # A, B, C
            fg, bg = DIR_COLORS[i] if i < len(DIR_COLORS) else (DIR_COLORS[0])
            self._dir_labels[d] = (letter, fg, bg)

        self._build_legend()
        self._populate_tree()

    def apply_filter(self, filter_value: str):
        """Filter displayed groups by type."""
        self._current_filter = filter_value
        self._checked.clear()
        self._selected_group_idx = None
        self._populate_tree()

    def _populate_tree(self):
        """Rebuild the treeview rows from data. Instant — no widget creation."""
        # Clear tree
        self._tree.delete(*self._tree.get_children())
        self._item_to_group.clear()
        self._groups.clear()
        self._clear_detail_panel()

        if not self._result:
            return

        if self._current_filter in (LABEL_FILTER_ALL, LABEL_FILTER_IDENTICAL):
            self._groups.extend(self._result.binary_duplicates)
        if self._current_filter in (LABEL_FILTER_ALL, LABEL_FILTER_MODIFIED):
            self._groups.extend(self._result.diverged_files)

        for i, group in enumerate(self._groups):
            type_label = LABEL_IDENTICAL if group.match_type == MatchType.BINARY_DUPLICATE else LABEL_MODIFIED
            size_str = format_size(group.files[0].size) if group.files else "--"
            sel_count = sum(1 for fi in range(len(group.files)) if (i, fi) in self._checked)
            sel_str = f"{sel_count}/{len(group.files)}" if sel_count > 0 else ""

            item_id = self._tree.insert(
                "",
                "end",
                values=(type_label, group.shared_name, len(group.files), size_str, sel_str),
            )
            self._item_to_group[item_id] = i

        self._update_floating_bar()

    # ---- Tree selection → detail panel ----

    def _on_tree_select(self, _event=None):
        """When a group is selected in the tree, show its files in the detail panel."""
        selection = self._tree.selection()
        if not selection:
            return

        item_id = selection[0]
        group_idx = self._item_to_group.get(item_id)
        if group_idx is None:
            return

        self._selected_group_idx = group_idx
        self._build_detail_panel(group_idx)

    def _clear_detail_panel(self):
        """Remove all file row widgets from the detail panel."""
        for w in self._file_row_widgets:
            w.destroy()
        self._file_row_widgets.clear()
        self._file_check_vars.clear()
        self._btn_select_except.pack_forget()
        self._btn_deselect.pack_forget()
        self._detail_header.configure(text="Select a group above to see its files")

    def _build_detail_panel(self, group_idx: int):
        """Build file rows for one group (typically 2-10 files — trivial)."""
        self._clear_detail_panel()
        group = self._groups[group_idx]
        is_identical = group.match_type == MatchType.BINARY_DUPLICATE

        # Header
        type_label = LABEL_IDENTICAL if is_identical else LABEL_MODIFIED
        accent = COLOR_GREEN if is_identical else COLOR_ORANGE
        self._detail_header.configure(
            text=f"  {type_label.upper()}  —  \"{group.shared_name}\"  —  {len(group.files)} copies",
            text_color=accent,
        )

        # Determine recommended keep
        recommended = group.newest_file

        # Sort files newest first
        sorted_files = sorted(group.files, key=lambda f: f.modified, reverse=True)

        for fi_sorted, file_rec in enumerate(sorted_files):
            # Find the original index in group.files
            fi = group.files.index(file_rec)
            is_keep = is_identical and (file_rec is recommended)
            is_checked = (group_idx, fi) in self._checked

            var = tk.BooleanVar(value=is_checked)
            self._file_check_vars.append(var)

            row = self._make_file_row(
                self._detail_scroll, file_rec, is_keep, var,
                lambda _v=var, _gi=group_idx, _fi=fi: self._on_file_check_toggle(_gi, _fi, _v),
            )
            row.pack(fill="x", pady=2, padx=5)
            self._file_row_widgets.append(row)

        # Action buttons
        if is_identical:
            self._btn_select_except.pack(side="left", padx=(0, 10))
        self._btn_deselect.pack(side="left")

    def _make_file_row(self, parent, file_rec: FileRecord, is_keep: bool, var: tk.BooleanVar, on_toggle):
        """Create a single file row widget (checkbox + dir badge + info + open button)."""
        # Determine directory identity
        dir_info = self._dir_labels.get(file_rec.directory_root)
        dir_letter = dir_info[0] if dir_info else "?"
        dir_fg = dir_info[1] if dir_info else COLOR_TEXT_SECONDARY
        dir_bg = dir_info[2] if dir_info else COLOR_SURFACE

        row = ctk.CTkFrame(parent, fg_color=dir_bg, corner_radius=6, border_width=1, border_color=COLOR_BORDER)

        cb = ctk.CTkCheckBox(
            row, text="", variable=var, width=24,
            checkbox_width=20, checkbox_height=20, command=on_toggle,
        )
        cb.pack(side="left", padx=(10, 5), pady=8)

        # Directory badge — prominent colored label showing A, B, or C
        dir_badge = ctk.CTkFrame(row, fg_color=dir_fg, corner_radius=4, width=36, height=36)
        dir_badge.pack(side="left", padx=(0, 8), pady=8)
        dir_badge.pack_propagate(False)
        ctk.CTkLabel(
            dir_badge, text=f"  {dir_letter}  ",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white",
        ).pack(expand=True)

        if is_keep:
            badge = ctk.CTkFrame(row, fg_color=COLOR_KEEP_BADGE_BG, corner_radius=4)
            ctk.CTkLabel(
                badge, text="KEEP",
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=COLOR_KEEP_BADGE_TEXT,
            ).pack(padx=6, pady=2)
            badge.pack(side="left", padx=(0, 8))

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=5, pady=8)

        # Line 1: Directory label + filename
        line1 = ctk.CTkFrame(info, fg_color="transparent")
        line1.pack(fill="x")
        ctk.CTkLabel(
            line1, text=f"DIR {dir_letter}:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=dir_fg, anchor="w",
        ).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            line1, text=file_rec.filename,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY, anchor="w",
        ).pack(side="left")

        # Line 2: full directory name + relative path
        ctk.CTkLabel(
            info, text=f"{file_rec.directory_root.name} / {file_rec.relative_path}",
            font=ctk.CTkFont(size=10),
            text_color=COLOR_TEXT_SECONDARY, anchor="w",
        ).pack(fill="x")

        # Line 3: size + date
        meta = f"{format_size(file_rec.size)}  \u2014  Modified: {format_date(file_rec.modified)}"
        ctk.CTkLabel(
            info, text=meta,
            font=ctk.CTkFont(size=10),
            text_color=COLOR_TEXT_TERTIARY, anchor="w",
        ).pack(fill="x")

        ctk.CTkButton(
            row, text="Open", width=50, height=28, fg_color="gray40",
            command=lambda f=file_rec: reveal_in_file_manager(f.path),
        ).pack(side="right", padx=10, pady=8)

        return row

    # ---- Checkbox handling ----

    def _on_file_check_toggle(self, group_idx: int, file_idx: int, var: tk.BooleanVar):
        """Toggle a file's checked state in the global set."""
        key = (group_idx, file_idx)
        if var.get():
            self._checked.add(key)
        else:
            self._checked.discard(key)
        self._update_tree_row_selection(group_idx)
        self._update_floating_bar()

    def _select_all_except_newest(self):
        """Check all files in the current group except the recommended keep."""
        if self._selected_group_idx is None:
            return
        gi = self._selected_group_idx
        group = self._groups[gi]
        recommended = group.newest_file
        for fi, f in enumerate(group.files):
            key = (gi, fi)
            if f is recommended:
                self._checked.discard(key)
            else:
                self._checked.add(key)
        # Refresh detail panel to update checkboxes
        self._build_detail_panel(gi)
        self._update_tree_row_selection(gi)
        self._update_floating_bar()

    def _deselect_group(self):
        """Uncheck all files in the current group."""
        if self._selected_group_idx is None:
            return
        gi = self._selected_group_idx
        group = self._groups[gi]
        for fi in range(len(group.files)):
            self._checked.discard((gi, fi))
        self._build_detail_panel(gi)
        self._update_tree_row_selection(gi)
        self._update_floating_bar()

    def _update_tree_row_selection(self, group_idx: int):
        """Update the 'Selected' column in the tree for a specific group."""
        group = self._groups[group_idx]
        sel_count = sum(1 for fi in range(len(group.files)) if (group_idx, fi) in self._checked)
        sel_str = f"{sel_count}/{len(group.files)}" if sel_count > 0 else ""

        # Find the tree item for this group
        for item_id, gi in self._item_to_group.items():
            if gi == group_idx:
                current = self._tree.item(item_id, "values")
                self._tree.item(item_id, values=(current[0], current[1], current[2], current[3], sel_str))
                break

    def _update_floating_bar(self):
        """Update the floating bar with total selected count and size."""
        total_count = 0
        total_bytes = 0
        for gi, fi in self._checked:
            if gi < len(self._groups):
                group = self._groups[gi]
                if fi < len(group.files):
                    total_count += 1
                    total_bytes += group.files[fi].size
        self._floating_bar.update_selection(total_count, total_bytes)

    # ---- Batch operations from toolbar ----

    def select_all_from_directory(self, directory: Path):
        """Check all files from a specific directory across all groups."""
        for gi, group in enumerate(self._groups):
            for fi, f in enumerate(group.files):
                if f.directory_root == directory:
                    self._checked.add((gi, fi))
        # Refresh detail panel if one is shown
        if self._selected_group_idx is not None:
            self._build_detail_panel(self._selected_group_idx)
        # Update all tree rows
        for gi in range(len(self._groups)):
            self._update_tree_row_selection(gi)
        self._update_floating_bar()

    # ---- Deletion ----

    def delete_selected(self):
        """Gather all checked files, confirm, and send to Recycle Bin."""
        selected_files: list[tuple[int, int, FileRecord]] = []
        for gi, fi in sorted(self._checked):
            if gi < len(self._groups):
                group = self._groups[gi]
                if fi < len(group.files):
                    selected_files.append((gi, fi, group.files[fi]))

        if not selected_files:
            return

        file_records = [f for _, _, f in selected_files]

        # Show confirmation dialog
        dialog = ConfirmDeleteDialog(self.winfo_toplevel(), file_records)
        self.wait_window(dialog)

        if not dialog.result:
            return

        from send2trash import send2trash

        deleted: list[tuple[int, int, FileRecord]] = []
        for gi, fi, f in selected_files:
            try:
                send2trash(str(f.path))
                deleted.append((gi, fi, f))
            except Exception:
                pass

        # Remove deleted files from groups and checked set
        groups_modified: set[int] = set()
        for gi, fi, f in reversed(deleted):
            self._checked.discard((gi, fi))
            group = self._groups[gi]
            group.files.remove(f)
            groups_modified.add(gi)

        # Re-index checked set after file removals
        new_checked: set[tuple[int, int]] = set()
        for gi, fi in self._checked:
            if gi < len(self._groups):
                group = self._groups[gi]
                if fi < len(group.files):
                    new_checked.add((gi, fi))
        self._checked = new_checked

        # Rebuild tree (groups with < 2 files are removed)
        self._groups = [g for g in self._groups if len(g.files) >= 2]
        self._selected_group_idx = None
        self._populate_tree()
