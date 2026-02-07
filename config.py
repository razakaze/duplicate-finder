"""Application constants and configuration."""

APP_NAME = "Duplicate File Finder"
APP_VERSION = "1.1.0"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 750
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 600

# Minimum directories required to start a scan
MIN_DIRECTORIES = 2
MAX_DIRECTORIES = 3

# --- Color Palette ---
COLOR_BG_WINDOW = "#1a1a2e"
COLOR_SURFACE = "#222240"
COLOR_SURFACE_HOVER = "#2a2a4a"
COLOR_SURFACE_SELECTED = "#2e3a5f"

COLOR_PRIMARY = "#4e9af1"
COLOR_PRIMARY_HOVER = "#3b82d4"

COLOR_GREEN = "#2ecc71"
COLOR_GREEN_BG = "#1a3a2a"
COLOR_ORANGE = "#f39c12"
COLOR_ORANGE_BG = "#3a2e1a"
COLOR_RED = "#e74c3c"
COLOR_RED_HOVER = "#c0392b"

COLOR_TEXT_PRIMARY = "#f0f0f5"
COLOR_TEXT_SECONDARY = "#9999b0"
COLOR_TEXT_TERTIARY = "#666680"
COLOR_BORDER = "#333355"

COLOR_KEEP_BADGE_BG = "#1e6f3e"
COLOR_KEEP_BADGE_TEXT = "#a8f0c6"

# Directory identity colors (A, B, C)
COLOR_DIR_A = "#4e9af1"       # Blue
COLOR_DIR_A_BG = "#1a2a4a"
COLOR_DIR_B = "#a855f7"       # Purple
COLOR_DIR_B_BG = "#2a1a3a"
COLOR_DIR_C = "#14b8a6"       # Teal
COLOR_DIR_C_BG = "#1a3a35"
DIR_COLORS = [
    (COLOR_DIR_A, COLOR_DIR_A_BG),
    (COLOR_DIR_B, COLOR_DIR_B_BG),
    (COLOR_DIR_C, COLOR_DIR_C_BG),
]

# --- User-facing labels (no jargon) ---
LABEL_IDENTICAL = "Identical Copy"
LABEL_MODIFIED = "Modified Version"
LABEL_FILTER_ALL = "All"
LABEL_FILTER_IDENTICAL = "Identical Copies"
LABEL_FILTER_MODIFIED = "Modified Versions"
