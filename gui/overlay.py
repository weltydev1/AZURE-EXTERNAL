from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QPushButton, QSlider, QLabel, QFrame, QHBoxLayout, QComboBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from core.utils import get_game_window_rect, is_insert_pressed
MENU_BACKGROUND = "#1e1e1e"
MENU_FOREGROUND = "#f0f0f0"
MENU_ACCENT = "#00bcd4"
MENU_HOVER = "#2a435a"
MENU_WIDTH = 550
MENU_HEIGHT = 650
QSS_STYLE = f"""
    QWidget {{
        background-color: transparent;
        color: {MENU_FOREGROUND};
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 11pt;
    }}
    #MenuFrame {{
        background-color: {MENU_BACKGROUND};
        border: 2px solid {MENU_ACCENT};
        border-radius: 10px;
    }}
    QTabWidget::pane {{
        border: 1px solid {MENU_ACCENT};
        border-top: 0px;
        background-color: {MENU_BACKGROUND};
        border-bottom-left-radius: 10px;
        border-bottom-right-radius: 10px;
    }}
    QTabBar::tab {{
        background: #2b2b2b;
        color: {MENU_FOREGROUND};
        padding: 10px 20px;
        min-width: 100px;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background: {MENU_ACCENT};
        color: {MENU_BACKGROUND};
        font-weight: bold;
    }}
    .ControlRow {{
        background-color: #242424;
        border-radius: 5px;
        margin: 3px 0;
        padding: 0px 10px;
        transition: background-color 0.3s ease;
    }}
    .ControlRow:hover {{
        background-color: {MENU_HOVER};
    }}
    .Switch {{
        border: none;
        border-radius: 14px;
        min-width: 60px;
        max-width: 60px;
        min-height: 28px;
        max-height: 28px;
        padding: 2px;
    }}
    .Switch:checked {{
        background-color: #2ecc71;
        padding-left: 32px;
    }}
    .Switch:!checked {{
        background-color: #e74c3c;
        padding-right: 32px;
    }}
    .Switch::indicator {{
        border-radius: 12px;
        border: 2px solid #f0f0f0;
        width: 24px;
        height: 24px;
        background-color: #f0f0f0;
        margin: 0px;
    }}
    QComboBox {{
        border: 1px solid #444444;
        border-radius: 5px;
        padding: 5px 10px 5px 10px;
        background-color: #2b2b2b;
        selection-background-color: {MENU_ACCENT};
        min-height: 30px;
        min-width: 150px;
    }}
    QComboBox:hover {{
        border-color: {MENU_ACCENT};
    }}
    QComboBox QAbstractItemView {{
        border: 1px solid {MENU_ACCENT};
        background-color: #2b2b2b;
        selection-background-color: {MENU_ACCENT};
        outline: 0;
    }}
    QSlider::groove:horizontal {{
        height: 8px;
        background: #3c3c3c;
        border: 1px solid #444444;
        margin: 0px 0;
        border-radius: 4px;
    }}
    QSlider::handle:horizontal {{
        background: {MENU_ACCENT};
        border: 1px solid #f0f0f0;
        width: 18px;
        height: 18px;
        margin: -5px 0;
        border-radius: 9px;
    }}
    QSlider::sub-page:horizontal {{
        background: {MENU_ACCENT};
        border-radius: 4px;
    }}
    QLabel {{
        padding: 5px 0px;
    }}
"""
class OverlayGUI(QWidget):
    def __init__(self, app, settings, player_positions, process_window_title):
        super().__init__()
        self.app = app
        self.SETTINGS = settings
        self.PLAYER_POSITIONS = player_positions
        self.PROCESS_WINDOW_TITLE = process_window_title
        self.setWindowTitle("AZURE EXTERNAL")
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.X11BypassWindowManagerHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setMouseTracking(True)
        self.setStyleSheet(QSS_STYLE)
        self.menu_visible = False
        self.setup_ui()
        self.overlay_timer = QTimer(self)
        self.overlay_timer.timeout.connect(self.update_overlay_loop)
        self.overlay_timer.start(10)
        self.insert_timer = QTimer(self)
        self.insert_timer.timeout.connect(self.check_insert_loop)
        self.insert_timer.start(100)
        self.toggle_menu_visibility(initial=True)
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.menu_frame = QFrame(self)
        self.menu_frame.setObjectName("MenuFrame")
        self.menu_frame.setFixedSize(MENU_WIDTH, MENU_HEIGHT)
        menu_layout = QVBoxLayout(self.menu_frame)
        menu_layout.setContentsMargins(15, 15, 15, 15)
        title = QLabel("AZURE EXTERNAL")
        title.setStyleSheet(f"font-size: 20pt; font-weight: bold; color: {MENU_ACCENT}; padding: 10px 0; border-bottom: 2px solid #2b2b2b; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignLeft)
        menu_layout.addWidget(title)
        self.notebook = QTabWidget(self.menu_frame)
        menu_layout.addWidget(self.notebook)
        self.build_aim_tab()
        self.build_visuals_tab()
        self.build_misc_tab()
        self.layout.addWidget(self.menu_frame, alignment=Qt.AlignCenter)
        self.menu_frame.hide()
    def wrap_layout_in_frame(self, parent_layout, inner_layout):
        frame = QFrame(self)
        frame.setProperty("class", "ControlRow")
        frame.setLayout(inner_layout)
        parent_layout.addWidget(frame)
        return frame
    def create_combobox(self, parent_layout, text, items, initial_key, callback):
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 5, 0, 5)
        label = QLabel(text)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        h_layout.addWidget(label)
        h_layout.addStretch(1)
        combobox = QComboBox(self)
        combobox.addItems(items)
        initial_index = items.index(initial_key)
        combobox.setCurrentIndex(initial_index)
        combobox.currentTextChanged.connect(callback)
        h_layout.addWidget(combobox)
        self.wrap_layout_in_frame(parent_layout, h_layout)
        return combobox
    def create_switch(self, parent_layout, text, initial_state, key):
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 5, 0, 5)
        label = QLabel(text)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        h_layout.addWidget(label)
        h_layout.addStretch(1)
        switch = QPushButton("")
        switch.setObjectName("switch_" + key)
        switch.setCheckable(True)
        switch.setChecked(initial_state)
        switch.setProperty("class", "Switch")
        def switch_state_changed(checked):
            self.toggle_setting(key, checked)
        switch.toggled.connect(switch_state_changed)
        h_layout.addWidget(switch)
        self.wrap_layout_in_frame(parent_layout, h_layout)
    def create_slider_with_label(self, parent_layout, text, min_val, max_val, initial_val, callback, step=1):
        v_layout = QVBoxLayout()
        v_layout.setContentsMargins(0, 5, 0, 5)
        h_label = QHBoxLayout()
        label_text = QLabel(text)
        label_text.setStyleSheet("font-weight: bold; padding: 5px 0;")
        h_label.addWidget(label_text)
        h_label.addStretch(1)
        val_label = QLabel()
        val_label.setFixedWidth(50)
        val_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        h_label.addWidget(val_label)
        v_layout.addLayout(h_label)
        h_control = QHBoxLayout()
        slider = QSlider(Qt.Horizontal)
        scale_factor = 10 if step < 1.0 else 1
        slider.setRange(int(min_val * scale_factor), int(max_val * scale_factor))
        def slider_callback(value):
            real_value = value / scale_factor
            if step < 1.0:
                val_label.setText(f"{real_value:.1f}")
            else:
                val_label.setText(f"{int(real_value):.0f}")
            callback(real_value)
        slider.valueChanged.connect(slider_callback)
        slider.setValue(int(initial_val * scale_factor))
        h_control.addWidget(slider)
        v_layout.addLayout(h_control)
        self.wrap_layout_in_frame(parent_layout, v_layout)
        return slider, val_label
    def build_aim_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        self.create_switch(layout, "Enable **Aimbot** (Hold LMB)", self.SETTINGS["AIM_ACTIVE"], "AIM_ACTIVE")
        self.create_switch(layout, "Enable **Wallhack** (WH)", self.SETTINGS["WH_ACTIVE"], "WH_ACTIVE")
        layout.addSpacing(15)
        self.create_combobox(layout, "Target **Hitbox**:", list(self.SETTINGS["HITBOX_OFFSETS"].keys()), self.SETTINGS["CURRENT_HITBOX_KEY"], self.update_hitbox)
        self.create_combobox(layout, "Aim **Priority**:", self.SETTINGS["AIM_PRIORITY_OPTIONS"], self.SETTINGS["CURRENT_AIM_PRIORITY"], self.update_aim_priority)
        layout.addSpacing(15)
        self.fov_slider, self.fov_label = self.create_slider_with_label(layout, "**Max FOV** (deg):", 1.0, 40.0, self.SETTINGS['MAX_FOV_DEGREES'], self.update_fov, step=0.1)
        self.dist_slider, self.dist_label = self.create_slider_with_label(layout, "**Max Distance** (units):", 500.0, 3000.0, self.SETTINGS['MAX_AIM_DISTANCE'], self.update_distance, step=100.0)
        self.smooth_slider, self.smooth_label = self.create_slider_with_label(layout, "**Smooth Factor** (1.0 = instant):", 1.0, 20.0, self.SETTINGS['AIM_SMOOTH_FACTOR'], self.update_smooth, step=0.1)
        layout.addStretch(1)
        self.notebook.addTab(tab, "Aimbot/WH")
    def build_visuals_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        self.create_switch(layout, "Draw **FOV Circle**", self.SETTINGS["OVERLAY_ACTIVE"], "OVERLAY_ACTIVE")
        layout.addSpacing(15)
        self.create_switch(layout, "Enable **2D Radar** (Top-Left)", self.SETTINGS["RADAR_ACTIVE"], "RADAR_ACTIVE")
        self.radar_range_slider, self.radar_range_label = self.create_slider_with_label(layout, "Radar **Range** (units):", 500.0, 3000.0, self.SETTINGS['RADAR_RANGE'], self.update_radar_range, step=100.0)
        self.radar_size_slider, self.radar_size_label = self.create_slider_with_label(layout, "Radar **Size** (px):", 50.0, 400.0, float(self.SETTINGS['RADAR_SIZE']), self.update_radar_size, step=10.0)
        layout.addStretch(1)
        self.notebook.addTab(tab, "Visuals")
    def build_misc_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        self.create_switch(layout, "Anti-Flash", self.SETTINGS["ANTIFLASH_ACTIVE"], "ANTIFLASH_ACTIVE")
        self.create_switch(layout, "BUNNYHOP", self.SETTINGS["BUNNYHOP_ACTIVE"], "BUNNYHOP_ACTIVE")
        layout.addStretch(1)
        self.notebook.addTab(tab, "Misc")
    def toggle_setting(self, key, value):
        self.SETTINGS[key] = value
    def update_hitbox(self, hitbox_key):
        self.SETTINGS["CURRENT_HITBOX_KEY"] = hitbox_key
        self.SETTINGS["HEAD_HEIGHT_OFFSET"] = self.SETTINGS["HITBOX_OFFSETS"][hitbox_key]
    def update_aim_priority(self, priority_key):
        self.SETTINGS["CURRENT_AIM_PRIORITY"] = priority_key
    def update_fov(self, value):
        self.SETTINGS["MAX_FOV_DEGREES"] = value
    def update_distance(self, value):
        self.SETTINGS["MAX_AIM_DISTANCE"] = value
    def update_smooth(self, value):
        self.SETTINGS["AIM_SMOOTH_FACTOR"] = value
    def update_radar_range(self, value):
        self.SETTINGS["RADAR_RANGE"] = value
    def update_radar_size(self, value):
        self.SETTINGS["RADAR_SIZE"] = int(value)
    def toggle_menu_visibility(self, initial=False):
        self.menu_visible = not self.menu_visible
        if self.menu_visible:
            self.menu_frame.show()
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowTransparentForInput)
        else:
            self.menu_frame.hide()
            self.setWindowFlags(self.windowFlags() | Qt.WindowTransparentForInput)
        if not initial:
            self.show()
    def check_insert_loop(self):
        if is_insert_pressed():
            self.toggle_menu_visibility()
    def update_overlay_loop(self):
        game_rect = get_game_window_rect(self.PROCESS_WINDOW_TITLE)
        if game_rect:
            x, y, w, h = game_rect
            self.setGeometry(x, y, w, h)
            if self.menu_visible:
                menu_w, menu_h = self.menu_frame.width(), self.menu_frame.height()
                self.menu_frame.move((w - menu_w) // 2, (h - menu_h) // 2)
            self.update()
        else:
            if not self.isHidden():
                self.hide()
    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.menu_visible:
            self.draw_watermark(painter)
            if self.SETTINGS["OVERLAY_ACTIVE"]:
                self.draw_fov_circle(painter)
            if self.SETTINGS["RADAR_ACTIVE"]:
                self.draw_radar(painter)
        painter.end()
    def draw_watermark(self, painter):
        text = "AZURE EXTERNAL"
        font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor(0, 188, 212), 1))
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.height()
        x = self.width() - text_width - 10
        y = 10 + text_height
        painter.drawText(x, y, text)
    def draw_fov_circle(self, painter):
        w, h = self.width(), self.height()
        center_x, center_y = w // 2, h // 2
        fov_radius = int(self.SETTINGS["MAX_FOV_DEGREES"] * (w / 100) / 2)
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center_x - fov_radius, center_y - fov_radius,
                            2 * fov_radius, 2 * fov_radius)
    def draw_radar(self, painter):
        radar_size = self.SETTINGS["RADAR_SIZE"]
        radar_range = self.SETTINGS["RADAR_RANGE"]
        radar_center_x = 50 + radar_size // 2
        radar_center_y = 50 + radar_size // 2
        painter.setPen(QPen(QColor(0, 188, 212), 2))
        painter.setBrush(QColor(30, 30, 30, 200))
        painter.drawEllipse(radar_center_x - radar_size // 2, radar_center_y - radar_size // 2,
                            radar_size, radar_size)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255))
        point_radius = 3
        painter.drawEllipse(radar_center_x - point_radius, radar_center_y - point_radius,
                            2 * point_radius, 2 * point_radius)
        scale_factor = radar_size / (2.0 * radar_range)
        point_radius = 4
        for player in self.PLAYER_POSITIONS:
            rel_x = player['x']
            rel_y = player['y']
            distance_sq = rel_x**2 + rel_y**2
            if distance_sq > radar_range**2:
                continue
            radar_x = int(radar_center_x + rel_y * scale_factor)
            radar_y = int(radar_center_y - rel_x * scale_factor)
            color = QColor(255, 0, 0) if player['is_enemy'] else QColor(0, 255, 0)
            painter.setBrush(color)
            painter.drawEllipse(radar_x - point_radius, radar_y - point_radius,
                                2 * point_radius, 2 * point_radius)
