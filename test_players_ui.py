# test_players_ui.py
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from ui.window import PlayerStatusWidget

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windrose Sync — Player Status UI Test Panel")
        self.setGeometry(100, 100, 500, 300)
        self.setStyleSheet("background-color: #0b1519;") # matches dark dashboard style

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header bar containing the widget
        header = QWidget()
        header.setStyleSheet("background-color: #0f1e24; border-radius: 8px;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(15, 10, 15, 10)

        title = QLabel("👥 Server Header Simulation")
        title.setFont(QFont("PT Sans", 11, QFont.Weight.Bold))
        title.setStyleSheet("color: #48C0A4; border: none;")
        hl.addWidget(title)
        hl.addStretch()

        # The Status Widget itself
        self.player_status = PlayerStatusWidget()
        hl.addWidget(self.player_status)
        layout.addWidget(header)

        # Active mock data
        self.mock_players = {}

        # Controls panel
        controls = QWidget()
        cl = QVBoxLayout(controls)
        cl.setSpacing(10)

        btn_font = QFont("PT Sans", 10, QFont.Weight.Bold)

        # Action 1: Add a Connecting Player
        self.btn_add_connecting = QPushButton("⏳ Step 1: Add 'Goth Ju' (Connecting, shows ID)")
        self.btn_add_connecting.setFont(btn_font)
        self.btn_add_connecting.setStyleSheet("background-color: #D99B26; color: #0F1E24; border-radius: 6px; padding: 8px; border: none;")
        self.btn_add_connecting.clicked.connect(self.mock_connecting)
        cl.addWidget(self.btn_add_connecting)

        # Action 2: Change Player to Connected (In Game)
        self.btn_connect = QPushButton("🟢 Step 2: Make 'Goth Ju' Connected (In Game, keeps ID)")
        self.btn_connect.setFont(btn_font)
        self.btn_connect.setStyleSheet("background-color: #48C0A4; color: #0F1E24; border-radius: 6px; padding: 8px; border: none;")
        self.btn_connect.clicked.connect(self.mock_connected)
        cl.addWidget(self.btn_connect)

        # Action 3: Add a Second Player
        self.btn_add_second = QPushButton("👥 Step 3: Add 'Rounak' (Connecting, shows ID)")
        self.btn_add_second.setFont(btn_font)
        self.btn_add_second.setStyleSheet("background-color: #3A86C8; color: #FFFFFF; border-radius: 6px; padding: 8px; border: none;")
        self.btn_add_second.clicked.connect(self.mock_add_second)
        cl.addWidget(self.btn_add_second)

        # Action 4: Clear all players (Disconnect)
        self.btn_clear = QPushButton("❌ Step 4: Disconnect All Players")
        self.btn_clear.setFont(btn_font)
        self.btn_clear.setStyleSheet("background-color: #E05C5C; color: #FFFFFF; border-radius: 6px; padding: 8px; border: none;")
        self.btn_clear.clicked.connect(self.mock_clear)
        cl.addWidget(self.btn_clear)

        layout.addWidget(controls)
        layout.addStretch()

        self.info_lbl = QLabel("Hover over the player icon + badge in the header after clicking actions!")
        self.info_lbl.setFont(QFont("PT Sans", 9, QFont.Weight.Medium))
        self.info_lbl.setStyleSheet("color: #839496; border: none;")
        self.info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_lbl)

    def mock_connecting(self):
        self.mock_players["F6335E064050D5A2481B77B09CA138F9"] = {
            "name": "Goth Ju",
            "state": "connecting"
        }
        self.player_status.update_players(self.mock_players)
        self.info_lbl.setText("Goth Ju added as ⏳ (Connecting) with ID: F6335E06.")

    def mock_connected(self):
        if "F6335E064050D5A2481B77B09CA138F9" in self.mock_players:
            self.mock_players["F6335E064050D5A2481B77B09CA138F9"]["state"] = "connected"
            self.player_status.update_players(self.mock_players)
            self.info_lbl.setText("Goth Ju status changed to 🟢 (In Game), still displaying ID: F6335E06.")

    def mock_add_second(self):
        self.mock_players["D8291A77E201B412A84D77E1208C349E"] = {
            "name": "Rounak",
            "state": "connecting"
        }
        self.player_status.update_players(self.mock_players)
        self.info_lbl.setText("Second player Rounak added as ⏳ (Connecting) with ID: D8291A77.")

    def mock_clear(self):
        self.mock_players.clear()
        self.player_status.update_players(self.mock_players)
        self.info_lbl.setText("All players disconnected. Header widget hidden.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TestWindow()
    win.show()
    sys.exit(app.exec())
