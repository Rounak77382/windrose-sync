# ui/window.py

from pathlib import Path
import sys
from PIL import Image, ImageFilter
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame
)
from PyQt6.QtGui import QPixmap, QImage, QFont, QIcon
from PyQt6.QtCore import Qt

from ui.theme import theme_colors, get_style_sheets

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windrose Sync - Control Panel")
        self.setFixedSize(900, 600)
        
        logo_path = Path(__file__).parent.parent / "assets" / "logo.svg"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))
        
    def load_background(self):
        bg_path = Path(__file__).parent.parent / "assets" / "windrose_wallpaper.png"
        if bg_path.exists():
            try:
                original = Image.open(bg_path)
                resized = original.resize((900, 600), Image.Resampling.LANCZOS)
                blurred = resized.filter(ImageFilter.GaussianBlur(4))
                
                # Dark overlay for readability (alpha 150)
                overlay = Image.new("RGBA", blurred.size, (15, 30, 36, 150))
                composed = Image.alpha_composite(blurred.convert("RGBA"), overlay)
                
                # Convert Pillow image to QImage
                data = composed.tobytes("raw", "RGBA")
                qimage = QImage(data, composed.size[0], composed.size[1], QImage.Format.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimage)
                
                # Set as background label behind central widget
                self.bg_label = QLabel(self)
                self.bg_label.setPixmap(pixmap)
                self.bg_label.setGeometry(0, 0, 900, 600)
                self.bg_label.lower()
            except Exception as e:
                print(f"Error loading background image: {e}")

    def setup_ui(self):
        sheets = get_style_sheets()
        
        # Central Widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        # Main vertical layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # --- Header Frame ---
        self.header_frame = QFrame()
        self.header_frame.setObjectName("headerFrame")
        self.header_frame.setStyleSheet(sheets["header"])
        self.header_frame.setFixedHeight(70)
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        # Support for PyInstaller dynamic paths
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(__file__).parent.parent
            
        logo_path = base_dir / "assets" / "logo.svg"
        if logo_path.exists():
            self.logo_lbl = QLabel()
            # Scale logo to 60x60 to make it bigger and use QPixmap directly to preserve original red colors
            logo_pixmap = QPixmap(str(logo_path)).scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_lbl.setPixmap(logo_pixmap)
            self.logo_lbl.setStyleSheet("border: none; background: transparent;")
            header_layout.addWidget(self.logo_lbl)
            header_layout.addSpacing(10)
        
        self.title_lbl = QLabel("Windrose Sync")
        title_font = QFont("PT Sans", 20, QFont.Weight.Bold)
        self.title_lbl.setFont(title_font)
        self.title_lbl.setStyleSheet(f"color: {theme_colors['accent_gold']}; border: none;")
        header_layout.addWidget(self.title_lbl)
        
        header_layout.addStretch()
        
        self.status_lbl = QLabel("● Checking status...")
        status_font = QFont("PT Sans", 12, QFont.Weight.Bold)
        self.status_lbl.setFont(status_font)
        self.status_lbl.setStyleSheet(f"color: {theme_colors['text_muted']}; border: none;")
        header_layout.addWidget(self.status_lbl)
        
        self.main_layout.addWidget(self.header_frame)
        
        # --- Body Layout (Side by Side) ---
        body_layout = QHBoxLayout()
        body_layout.setSpacing(15)
        
        # Left Controls Frame
        self.controls_frame = QFrame()
        self.controls_frame.setObjectName("controlsFrame")
        self.controls_frame.setStyleSheet(sheets["controls"])
        self.controls_frame.setFixedWidth(250)
        
        controls_layout = QVBoxLayout(self.controls_frame)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        controls_layout.setSpacing(15)
        
        ctrl_title = QLabel("Controls")
        ctrl_title_font = QFont("PT Sans", 14, QFont.Weight.Bold)
        ctrl_title.setFont(ctrl_title_font)
        ctrl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ctrl_title.setStyleSheet(f"color: {theme_colors['text_main']}; border: none;")
        controls_layout.addWidget(ctrl_title)
        
        self.btn_start = QPushButton("Start Server & Sync")
        self.btn_start.setObjectName("btnStart")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setStyleSheet(sheets["btn_start"])
        controls_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("Stop Safely")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setStyleSheet(sheets["btn_stop"])
        controls_layout.addWidget(self.btn_stop)
        
        controls_layout.addSpacing(15)
        
        # --- Utility Buttons ---
        self.btn_start_game = QPushButton("Launch Game")
        self.btn_start_game.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start_game.setStyleSheet(sheets["btn_utility"])
        controls_layout.addWidget(self.btn_start_game)
        
        self.btn_open_drive = QPushButton("Open Google Drive")
        self.btn_open_drive.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_drive.setStyleSheet(sheets["btn_utility"])
        controls_layout.addWidget(self.btn_open_drive)
        
        self.btn_open_dir = QPushButton("Open Server Folder")
        self.btn_open_dir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_dir.setStyleSheet(sheets["btn_utility"])
        controls_layout.addWidget(self.btn_open_dir)
        
        controls_layout.addStretch()
        
        self.btn_unlock = QPushButton("Force Unlock")
        self.btn_unlock.setObjectName("btnUnlock")
        self.btn_unlock.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_unlock.setStyleSheet(sheets["btn_unlock"])
        controls_layout.addWidget(self.btn_unlock)
        
        body_layout.addWidget(self.controls_frame)
        
        # Right Logs Frame
        self.logs_frame = QFrame()
        self.logs_frame.setObjectName("logsFrame")
        self.logs_frame.setStyleSheet(sheets["logs"])
        
        logs_layout = QVBoxLayout(self.logs_frame)
        logs_layout.setContentsMargins(15, 15, 15, 15)
        
        self.log_textbox = QTextEdit()
        self.log_textbox.setObjectName("logBox")
        self.log_textbox.setReadOnly(True)
        self.log_textbox.setUndoRedoEnabled(False)
        self.log_textbox.setStyleSheet(sheets["log_box"])
        self.log_textbox.append("Welcome to Windrose Sync Control Panel.\n")
        logs_layout.addWidget(self.log_textbox)
        
        body_layout.addWidget(self.logs_frame)
        
        self.main_layout.addLayout(body_layout)
