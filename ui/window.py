# ui/window.py

from pathlib import Path
import sys
from PIL import Image, ImageFilter
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame, QApplication, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QImage, QFont, QIcon
from PyQt6.QtCore import Qt, QTimer, QPoint, QEvent

from ui.theme import theme_colors, get_style_sheets


class PlayerIconWidget(QWidget):
    """A premium, high-fidelity drawn vector icon representing players online."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(26, 26)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QBrush, QColor, QPainterPath
        painter = QPainter()
        if not painter.begin(self):
            return
        
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Proportional responsive vector scaling
            scale_factor = self.width() / 22.0
            painter.scale(scale_factor, scale_factor)

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
        finally:
            painter.end()

class LockStatusIcon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 22)
        self.color = "#48C0A4"

    def set_status_color(self, color):
        if self.color != color:
            self.color = color
            self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QPen
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        color = QColor(self.color)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Draw shackle (arch)
        painter.drawArc(5, 3, 12, 12, 0, 180*16)
        
        # Draw lock body
        painter.setBrush(color)
        painter.drawRoundedRect(4, 10, 14, 10, 2, 2)
        
        # Keyhole dot
        painter.setBrush(QColor("#0F1E24"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(10, 13, 2, 3)
        painter.end()

class ServerStatusIcon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 22)
        self.color = "#48C0A4"

    def set_status_color(self, color):
        if self.color != color:
            self.color = color
            self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        color = QColor(self.color)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)

        # Draw server blades stacked
        painter.drawRoundedRect(3, 4, 16, 4, 1, 1)
        painter.drawRoundedRect(3, 10, 16, 4, 1, 1)
        painter.drawRoundedRect(3, 16, 16, 4, 1, 1)
        
        # Tiny status leds
        painter.setBrush(QColor("#0F1E24"))
        painter.drawEllipse(5, 5, 2, 2)
        painter.drawEllipse(5, 11, 2, 2)
        painter.drawEllipse(5, 17, 2, 2)
        painter.end()

class CloudStatusIcon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 22)
        self.color = "#48C0A4"

    def set_status_color(self, color):
        if self.color != color:
            self.color = color
            self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QPainterPath
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        color = QColor(self.color)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)

        # Vector Cloud
        path = QPainterPath()
        path.addEllipse(4, 10, 8, 8)
        path.addEllipse(10, 10, 8, 8)
        path.addEllipse(7, 5, 9, 9)
        path.addRoundedRect(7, 12, 8, 6, 1, 1)
        
        painter.drawPath(path)
        painter.end()

class DashboardStatusTile(QWidget):
    """A composite status badge used in the global header containing a vector icon and dynamic labels."""
    def __init__(self, title_text, icon_widget, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)
        
        self.icon = icon_widget
        layout.addWidget(self.icon, 0, Qt.AlignmentFlag.AlignVCenter)
        
        text_container = QVBoxLayout()
        text_container.setSpacing(0)
        text_container.setContentsMargins(0,0,0,0)
        
        self.title_lbl = QLabel(title_text.upper())
        self.title_lbl.setFont(QFont("PT Sans", 8, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet(f"color: {theme_colors['text_muted']}; border: none; background: transparent;")
        self.title_lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        self.value_lbl = QLabel("INITIALIZING...")
        self.value_lbl.setFont(QFont("PT Sans", 9, QFont.Weight.Bold))
        self.value_lbl.setStyleSheet(f"color: {theme_colors['text_main']}; border: none; background: transparent;")
        self.value_lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        text_container.addWidget(self.title_lbl)
        text_container.addWidget(self.value_lbl)
        
        layout.addLayout(text_container)
        layout.addStretch()

    def update_status(self, text, hex_color):
        self.value_lbl.setText(text.upper())
        self.value_lbl.setStyleSheet(f"color: {hex_color}; border: none; background: transparent;")
        self.icon.set_status_color(hex_color)


class PlayerStatusWidget(QWidget):
    """Header widget: player icon + count badge. Hover reveals a dropdown with each player's state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._players = {}   # {id: {"name": str, "state": str}}
        self._popup  = None

        self.setFixedSize(34, 30)

        # Hover checking timer (checks if cursor has left both widget and popup)
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._check_hover)

        # Use beautiful premium vector icon parented directly to self
        self.icon_lbl = PlayerIconWidget(self)
        self.icon_lbl.move(0, 4)

        self.badge = QLabel("0", self)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setFixedSize(16, 16)
        self.badge.setFont(QFont("PT Sans", 8, QFont.Weight.Bold))
        self.badge.setStyleSheet(
            "color:#0F1E24; background:#48C0A4; border-radius:8px; border:none; padding-bottom:1px;"
        )
        self.badge.move(18, 0)

        self.setVisible(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ── public API ──────────────────────────────────────────────────────────
    def update_players(self, players: dict):
        self._players = dict(players)
        n = len(players)
        self.badge.setText(str(n))
        if self._popup and self._popup.isVisible():
            self._show_popup()   # rebuild in-place

    # ── hover logic ─────────────────────────────────────────────────────────
    def enterEvent(self, event):
        self._show_popup()
        self._timer.start()
        super().enterEvent(event)

    def _check_hover(self):
        """Deterministically verify if mouse is still hovering either the badge or the dropdown."""
        from PyQt6.QtGui import QCursor
        
        # Check main badge widget
        gp_widget = self.mapToGlobal(QPoint(0, 0))
        widget_rect = self.rect().translated(gp_widget)
        
        over_widget = widget_rect.contains(QCursor.pos())

        # Check dropdown popup widget (add a small 8px padding buffer so moving mouse between them is smooth)
        over_popup = False
        if self._popup and self._popup.isVisible():
            gp_popup = self._popup.mapToGlobal(QPoint(0, 0))
            popup_rect = self._popup.rect().translated(gp_popup)
            # Add small top buffer so moving through the tiny 4px gap doesn't cause a flicker
            popup_rect.adjust(0, -8, 0, 0)
            over_popup = popup_rect.contains(QCursor.pos())

        if not over_widget and not over_popup:
            self._hide_popup()
            self._timer.stop()

    # ── popup build ─────────────────────────────────────────────────────────
    def _show_popup(self):
        self._hide_popup()

        from PyQt6.QtWidgets import QWidget
        popup = QWidget(None)
        popup.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        popup.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Outer layout for popup
        outer_layout = QVBoxLayout(popup)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Styled container frame for background & rounded corners
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #0F1E24;
                border: 1px solid #48C0A4;
                border-radius: 8px;
            }
            QLabel { border: none; background: transparent; }
        """)
        outer_layout.addWidget(container)

        vbox = QVBoxLayout(container)
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

        if not self._players:
            no_players = QLabel("No players online")
            no_players.setFont(QFont("PT Sans", 9, QFont.Weight.Medium))
            no_players.setStyleSheet("color: #839496; padding: 4px 0;")
            vbox.addWidget(no_players)
        else:
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
                    ico.setStyleSheet("font-size: 10px; border: none; background: transparent;") # small green circle
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
        
        # Premium Glassmorphic Tooltip Styling
        self.setStyleSheet(f"""
            QToolTip {{
                background-color: #17303A;
                color: {theme_colors['text_main']};
                border: 1px solid {theme_colors['accent_gold']};
                border-radius: 4px;
                padding: 6px;
                font-family: 'PT Sans';
                font-size: 12px;
            }}
        """)
        
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
        
        header_layout.addSpacing(20)
        
        # Stylized Floating Vertical Separator
        line = QFrame()
        line.setFixedWidth(1)
        line.setMaximumHeight(32)
        line.setStyleSheet("background-color: #2A4A56; border: none;")
        header_layout.addWidget(line)
        
        header_layout.addSpacing(10)

        # Advanced System Metrics Header Section - Clustered Left
        self.tile_lock = DashboardStatusTile("Cloud Remote", LockStatusIcon())
        header_layout.addWidget(self.tile_lock)
        
        self.tile_server = DashboardStatusTile("Local Server", ServerStatusIcon())
        header_layout.addWidget(self.tile_server)
        
        self.tile_data = DashboardStatusTile("Backup Integrity", CloudStatusIcon())
        header_layout.addWidget(self.tile_data)
        
        # Push everything that follows to the absolute right extremity
        header_layout.addStretch()
        
        self.player_status = PlayerStatusWidget()
        header_layout.addWidget(self.player_status)
        
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
        self.btn_start.setToolTip("Safely downloads the latest cloud snapshot and starts the dedicated game server.")
        controls_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("Stop & Sync Safely")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setStyleSheet(sheets["btn_stop"])
        self.btn_stop.setToolTip("Exits the server process and triggers an immediate, automatic cloud backup.")
        controls_layout.addWidget(self.btn_stop)
        
        controls_layout.addSpacing(15)
        
        # --- Utility Buttons ---
        self.btn_manual_sync = QPushButton("Force Upload Save")
        self.btn_manual_sync.setObjectName("btnManualSync")
        self.btn_manual_sync.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_manual_sync.setStyleSheet(sheets["btn_utility"])
        self.btn_manual_sync.setToolTip("Manually initiates an upload of your local save files to the cloud.")
        controls_layout.addWidget(self.btn_manual_sync)

        self.btn_manual_fetch = QPushButton("Force Fetch Latest")
        self.btn_manual_fetch.setObjectName("btnManualFetch")
        self.btn_manual_fetch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_manual_fetch.setStyleSheet(sheets["btn_utility"])
        self.btn_manual_fetch.setToolTip("Overwrites local files with the latest version from the cloud.")
        controls_layout.addWidget(self.btn_manual_fetch)

        self.btn_start_game = QPushButton("Launch Game")
        self.btn_start_game.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start_game.setStyleSheet(sheets["btn_utility"])
        self.btn_start_game.setToolTip("Launches the configured game client executable for instant access.")
        controls_layout.addWidget(self.btn_start_game)
        
        self.btn_open_drive = QPushButton("Open Google Drive")
        self.btn_open_drive.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_drive.setStyleSheet(sheets["btn_utility"])
        self.btn_open_drive.setToolTip("Opens the remote cloud repository web portal in your browser.")
        controls_layout.addWidget(self.btn_open_drive)
        
        self.btn_open_dir = QPushButton("Open Server Folder")
        self.btn_open_dir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_dir.setStyleSheet(sheets["btn_utility"])
        self.btn_open_dir.setToolTip("Opens your local host file tree directly in File Explorer.")
        controls_layout.addWidget(self.btn_open_dir)
        
        controls_layout.addStretch()
        
        self.btn_unlock = QPushButton("Force Unlock")
        self.btn_unlock.setObjectName("btnUnlock")
        self.btn_unlock.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_unlock.setStyleSheet(sheets["btn_unlock"])
        self.btn_unlock.setToolTip("⚠️ EMERGENCY: Clears the cloud activity lock if a previous host crashed abnormally.")
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
