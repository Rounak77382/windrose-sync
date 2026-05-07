# ui/theme.py

theme_colors = {
    "bg_main": "#0F1E24",       # Deep sea abyss
    "bg_panel_rgba": "rgba(23, 48, 58, 160)",  # Translucent weathered hull teal
    "accent_gold": "#D99B26",    # Sunbaked brass gold
    "accent_gold_hover": "#B87F1A",
    "danger": "#9B2226",        # Crimson sailor's blood red
    "danger_hover": "#AE2012",
    "text_main": "#F4F0EA",      # Bleached driftwood parchment
    "text_muted": "#9FB1B7",    # Sea-salted muted teal-grey
    "status_idle": "#48C0A4",    # Tropical sea foam green
    "status_running": "#FFCC00"  # Brilliant caribbean sun yellow
}

def get_style_sheets():
    return {
        "header": f"""
            QFrame#headerFrame {{
                background-color: {theme_colors["bg_panel_rgba"]};
                border: 2px solid #17303A;
                border-radius: 10px;
            }}
        """,
        "controls": f"""
            QFrame#controlsFrame {{
                background-color: {theme_colors["bg_panel_rgba"]};
                border: 2px solid #17303A;
                border-radius: 10px;
            }}
        """,
        "btn_start": f"""
            QPushButton#btnStart {{
                background-color: {theme_colors["accent_gold"]};
                color: #000000;
                border: none;
                border-radius: 5px;
                font-family: 'PT Sans';
                font-weight: bold;
                font-size: 13px;
                padding: 10px;
            }}
            QPushButton#btnStart:hover {{
                background-color: {theme_colors["accent_gold_hover"]};
            }}
            QPushButton#btnStart:disabled {{
                background-color: #555555;
                color: #888888;
            }}
        """,
        "btn_stop": f"""
            QPushButton#btnStop {{
                background-color: {theme_colors["danger"]};
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                font-family: 'PT Sans';
                font-weight: bold;
                font-size: 13px;
                padding: 10px;
            }}
            QPushButton#btnStop:hover {{
                background-color: {theme_colors["danger_hover"]};
            }}
        """,
        "btn_unlock": f"""
            QPushButton#btnUnlock {{
                background-color: transparent;
                border: 2px solid {theme_colors["danger"]};
                color: {theme_colors["danger"]};
                border-radius: 5px;
                font-family: 'PT Sans';
                font-weight: bold;
                font-size: 13px;
                padding: 10px;
            }}
            QPushButton#btnUnlock:hover {{
                background-color: #3A1E24;
            }}
        """,
        "btn_utility": f"""
            QPushButton {{
                background-color: rgba(23, 48, 58, 200);
                color: {theme_colors["text_muted"]};
                border: 1px solid #48C0A4;
                border-radius: 5px;
                font-family: 'PT Sans';
                font-weight: bold;
                font-size: 12px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: #1A3A45;
                border: 1px solid {theme_colors["accent_gold"]};
                color: {theme_colors["accent_gold"]};
            }}
        """,
        "logs": f"""
            QFrame#logsFrame {{
                background-color: {theme_colors["bg_panel_rgba"]};
                border: 2px solid #17303A;
                border-radius: 10px;
            }}
        """,
        "log_box": f"""
            QTextEdit#logBox {{
                background-color: rgba(10, 20, 24, 180);
                color: {theme_colors["status_idle"]};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: none;
                border-radius: 5px;
            }}
        """
    }

def load_pt_sans():
    import urllib.request
    from pathlib import Path
    from PyQt6.QtGui import QFontDatabase
    
    import sys
    
    if getattr(sys, 'frozen', False):
        font_dir = Path(sys._MEIPASS) / "ui" / "fonts"
    else:
        font_dir = Path(__file__).parent / "fonts"
        
    font_dir.mkdir(parents=True, exist_ok=True)
    
    regular_path = font_dir / "PT_Sans-Web-Regular.ttf"
    bold_path = font_dir / "PT_Sans-Web-Bold.ttf"
    
    # Download if not present
    if not regular_path.exists():
        try:
            url = "https://raw.githubusercontent.com/google/fonts/main/ofl/ptsans/PT_Sans-Web-Regular.ttf"
            urllib.request.urlretrieve(url, regular_path)
        except Exception as e:
            print(f"Failed to download PT Sans Regular: {e}")
            
    if not bold_path.exists():
        try:
            url = "https://raw.githubusercontent.com/google/fonts/main/ofl/ptsans/PT_Sans-Web-Bold.ttf"
            urllib.request.urlretrieve(url, bold_path)
        except Exception as e:
            print(f"Failed to download PT Sans Bold: {e}")
            
    # Load into Qt font database
    if regular_path.exists():
        QFontDatabase.addApplicationFont(str(regular_path))
    if bold_path.exists():
        QFontDatabase.addApplicationFont(str(bold_path))
