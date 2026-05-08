# ui/window.py

from pathlib import Path
import sys
from PIL import Image, ImageFilter
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame, QApplication
)
from PyQt6.QtGui import QPixmap, QImage, QFont, QIcon
from PyQt6.QtCore import Qt, QTimer, QPoint, QEvent

from ui.theme import theme_colors, get_style_sheets


class PlayerIconWidget(QWidget):
    """A premium, high-fidelity drawn vector icon representing players online."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 22)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QBrush, QColor, QPainterPath
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor("#48C0A4") # Premium windrose-sync teal

        # Draw Back Player (slightly offset and translucent)
        painter.setOpacity(0.55)
        painter.drawEllipse(3, 4, 6, 6) # head
        path_back = QPainterPath()
        path_back.moveTo(0, 17)
        path_back.arcTo(0, 11, 12, 10, 0, 180)
        path_back.lineTo(0, 17)
        painter.drawPath(path_back)

        # Draw Front Player (prominent and fully opaque)
        painter.setOpacity(1.0)
        painter.drawEllipse(9, 2, 7, 7) # head
        path_front = QPainterPath()
        path_front.moveTo(5, 17)
        path_front.arcTo(5, 10, 15, 12, 0, 180)
        path_front.lineTo(5, 17)
        painter.drawPath(path_front)


class PlayerStatusWidget(QWidget):
    """Header widget: player icon + count badge. Hover reveals a dropdown with each player's state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._players = {}   # {id: {"name": str, "state": str}}
        self._popup  = None

        # Hide timer — delays hiding so mouse can move into popup
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._hide_popup)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(6)

        # Use beautiful premium vector icon
        self.icon_lbl = PlayerIconWidget()

        self.badge = QLabel("0")
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setFixedSize(22, 22)
        self.badge.setFont(QFont("PT Sans", 9, QFont.Weight.Bold))
        self.badge.setStyleSheet(
            "color:#0F1E24; background:#48C0A4; border-radius:11px; border:none;"
        )

        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.badge)
        self.setVisible(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ── public API ──────────────────────────────────────────────────────────
    def update_players(self, players: dict):
        self._players = dict(players)
        n = len(players)
        self.badge.setText(str(n))
        self.setVisible(n > 0)
        if self._popup and self._popup.isVisible():
            self._show_popup()   # rebuild in-place

    # ── hover logic ─────────────────────────────────────────────────────────
    def enterEvent(self, event):
        self._timer.stop()
        self._show_popup()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._timer.start()
        super().leaveEvent(event)

    def eventFilter(self, obj, event):
        """Keep popup open while mouse is inside it."""
        if event.type() == QEvent.Type.Enter:
            self._timer.stop()
        elif event.type() == QEvent.Type.Leave:
            self._timer.start()
        return False

    # ── popup build ─────────────────────────────────────────────────────────
    def _show_popup(self):
        if not self._players:
            return
        self._hide_popup()

        popup = QFrame(None)
        popup.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        popup.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        popup.setStyleSheet("""
            QFrame {
                background-color: #0F1E24;
                border: 1px solid #48C0A4;
                border-radius: 8px;
            }
            QLabel { border: none; background: transparent; }
        """)

        vbox = QVBoxLayout(popup)
        vbox.setContentsMargins(14, 10, 16, 12)
        vbox.setSpacing(8)

        # Title
        title = QLabel(f"Players Online")
        title.setFont(QFont("PT Sans", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #48C0A4;")
        vbox.addWidget(title)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:#2A4A56; max-height:1px; border:none;")
        vbox.addWidget(sep)

        for pid, info in self._players.items():
            state = info.get("state", "connecting")

            row = QWidget()
            row.setStyleSheet("background:transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 2, 0, 2)
            rl.setSpacing(8)

            # Indicators (⏳ and 🟢) as requested
            ico = QLabel()
            
            if state == "connected":
                ico.setText("🟢")
                ico.setStyleSheet("font-size: 7px; border: none; background: transparent;") # small green circle
                state_text = f"ID: {pid[:8]}"
                state_color = "#48C0A4"
            else:
                ico.setText("⏳")
                ico.setStyleSheet("font-size: 11px; border: none; background: transparent;")
                state_text = f"ID: {pid[:8]}"
                state_color = "#D99B26"

            nm = QLabel(info["name"])
            nm.setFont(QFont("PT Sans", 10, QFont.Weight.Bold))
            nm.setStyleSheet("color:#F4F0EA;")

            st = QLabel(state_text)
            st.setFont(QFont("PT Sans", 9))
            st.setStyleSheet(f"color:{state_color};")

            rl.addWidget(ico)
            rl.addWidget(nm)
            rl.addStretch()
            rl.addWidget(st)
            vbox.addWidget(row)

        popup.adjustSize()

        # Position below the widget
        gp = self.mapToGlobal(QPoint(0, self.height() + 4))
        popup.move(gp)
        popup.show()

        # Install event filter on popup + children to cancel hide timer
        popup.installEventFilter(self)
        for child in popup.findChildren(QWidget):
            child.installEventFilter(self)

        self._popup = popup

    def _hide_popup(self):
        if self._popup:
            self._popup.close()
            self._popup = None


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
        
        self.player_status = PlayerStatusWidget()
        header_layout.addWidget(self.player_status)
        
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
