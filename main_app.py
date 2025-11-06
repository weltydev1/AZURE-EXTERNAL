import sys
import threading
from PyQt5.QtWidgets import QApplication
from config import SETTINGS, PLAYER_POSITIONS, PROCESS_WINDOW_TITLE
from modules.aimbot import aimbot_loop
from gui.overlay import OverlayGUI
if __name__ == "__main__":
    aimbot_thread = threading.Thread(target=aimbot_loop, daemon=True)
    aimbot_thread.start()
    app = QApplication(sys.argv)
    gui = OverlayGUI(app, SETTINGS, PLAYER_POSITIONS, PROCESS_WINDOW_TITLE)
    gui.show()
    print("Azure started")
    sys.exit(app.exec_())
