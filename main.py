import sys
import json
import os
import pygame
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTimeEdit, QComboBox, QSpacerItem, QSizePolicy, QDesktopWidget, QMessageBox, QActionGroup, QAction)
from PyQt5.QtCore import QTimer, Qt, QTime, QElapsedTimer, QStandardPaths

from sound import SoundManager

def resource_path(relative_path):
    """개발 및 PyInstaller에 대해 리소스의 절대 경로를 가져옵니다."""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        pygame.mixer.init()
        if not pygame.mixer.get_init():
            print("Pygame mixer initialization failed!")
        else:
            print("Pygame mixer initialized successfully.")
        self.background_color = 'black'
        self.text_color = 'red'
        self.sounds = []
        self.sounds_file = os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), "sounds.json")
        self.user_sounds_folder = os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), "user_sounds")
        self.is_timer_mode = True
        self.setup_sound_folders()
        self.load_sounds()
        self.time_format = 'mm:ss'
        self.initUI()
        self.played_alarms = set()  # 재생된 알람을 추적하기 위한 집합

    def setup_sound_folders(self):
        if not os.path.exists(self.user_sounds_folder):
            os.makedirs(self.user_sounds_folder)
        if not os.path.exists(self.sounds_file):
            with open(self.sounds_file, 'w') as f:
                json.dump([], f)  # 빈 리스트를 저장하여 기본 구조 생성

    def load_sounds(self):
        if os.path.exists(self.sounds_file):
            try:
                with open(self.sounds_file, 'r') as f:
                    self.sounds = json.load(f)
                    if not self.sounds:  # 파일이 비어있다면, 빈 리스트로 초기화
                        self.sounds = []
            except json.JSONDecodeError:
                self.sounds = []
        else:
            self.sounds = []

    def save_sounds(self):
        with open(self.sounds_file, 'w') as f:
            json.dump(self.sounds, f, indent=4)

    def initUI(self):
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.elapsed_timer = QElapsedTimer()

        self.main_layout = QVBoxLayout(self.centralWidget)

        self.timer_container = QWidget(self.centralWidget)
        self.timer_container.setStyleSheet("background-color: black;")
        self.timer_container_layout = QVBoxLayout(self.timer_container)

        self.time_input = QTimeEdit(QTime(0, 0, 0), self.timer_container)
        self.time_input.setAlignment(Qt.AlignCenter)
        self.time_input.setDisplayFormat("HH:mm:ss")
        self.time_input.setStyleSheet("""
            QTimeEdit {
                font-size: 300px; 
                height: 100%; 
                background-color: black; 
                color: red;
            }
            QTimeEdit::up-button {
                width: 30px;
                height: 30px;
            }
            QTimeEdit::down-button {
                width: 30px;
                height: 30px;
            }
            QTimeEdit::up-arrow {
                width: 20px;
                height: 20px;
            }
            QTimeEdit::down-arrow {
                width: 20px;
                height: 20px;
            }
        """)
        self.time_input.setFixedHeight(300)
        self.set_time_format(self.time_format)

        self.update_spacers()
        self.main_layout.addWidget(self.timer_container)

        self.control_layout = QHBoxLayout()
        self.start_button = QPushButton('Start', self)
        self.start_button.setStyleSheet("font-size: 30px;")
        self.start_button.clicked.connect(self.start_timer)
        self.control_layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Stop', self)
        self.stop_button.setStyleSheet("font-size: 30px;")
        self.stop_button.clicked.connect(self.stop_timer)
        self.control_layout.addWidget(self.stop_button)

        self.reset_button = QPushButton('리셋', self)
        self.reset_button.setStyleSheet("font-size: 30px; color: black; background-color: white;")
        self.reset_button.clicked.connect(self.reset_timer)
        self.control_layout.addWidget(self.reset_button)

        self.main_layout.addLayout(self.control_layout)

        self.alarm_layout = QHBoxLayout()

        start_alarm_label = QLabel('시작 알람:', self)
        start_alarm_label.setStyleSheet("font-size: 20px;")
        self.alarm_layout.addWidget(start_alarm_label)

        self.start_alarm_input = QComboBox(self)
        self.start_alarm_input.setStyleSheet("font-size: 20px;")
        self.alarm_layout.addWidget(self.start_alarm_input)

        one_minute_before_label = QLabel('종료 1분 전 알람:', self)
        one_minute_before_label.setStyleSheet("font-size: 20px;")
        self.alarm_layout.addWidget(one_minute_before_label)

        self.one_minute_before_input = QComboBox(self)
        self.one_minute_before_input.setStyleSheet("font-size: 20px;")
        self.alarm_layout.addWidget(self.one_minute_before_input)

        end_alarm_label = QLabel('종료 알람:', self)
        end_alarm_label.setStyleSheet("font-size: 20px;")
        self.alarm_layout.addWidget(end_alarm_label)

        self.end_alarm_input = QComboBox(self)
        self.end_alarm_input.setStyleSheet("font-size: 20px;")
        self.alarm_layout.addWidget(self.end_alarm_input)

        self.main_layout.addLayout(self.alarm_layout)

        self.update_alarm_sounds()

        self.setWindowTitle('카운트다운 알람')
        self.resize_to_70_percent()
        self.create_menu()
        self.show()

        self.time_left = 0
        self.alarms = []

    def validate_time_input(self):
        text = self.time_input.text()
        if self.time_format == 'mm:ss':
            parts = text.split(':')
            if len(parts) != 2 or not all(part.isdigit() for part in parts):
                QMessageBox.warning(self, 'Error', '올바른 시간 형식이 아닙니다. (mm:ss)')
                self.time_input.setTime(QTime(0, 0))
        elif self.time_format == 'hh:mm:ss':
            parts = text.split(':')
            if len(parts) != 3 or not all(part.isdigit() for part in parts):
                QMessageBox.warning(self, 'Error', '올바른 시간 형식이 아닙니다. (hh:mm:ss)')
                self.time_input.setTime(QTime(0, 0, 0))

    def update_spacers(self):
        if hasattr(self, 'top_spacer'):
            self.timer_container_layout.removeItem(self.top_spacer)
        if hasattr(self, 'bottom_spacer'):
            self.timer_container_layout.removeItem(self.bottom_spacer)

        desktop = QDesktopWidget().availableGeometry(self)
        screen_height = desktop.height()

        spacer_height = (screen_height - 100) / 2

        self.top_spacer = QSpacerItem(20, int(spacer_height), QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.bottom_spacer = QSpacerItem(20, int(spacer_height), QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.timer_container_layout.addItem(self.top_spacer)
        self.timer_container_layout.addWidget(self.time_input, alignment=Qt.AlignCenter)
        self.timer_container_layout.addItem(self.bottom_spacer)

    def create_menu(self):
        menubar = self.menuBar()

        edit_menu = menubar.addMenu('편집')

        manage_sounds_action = edit_menu.addAction('음원 설정')
        manage_sounds_action.triggered.connect(self.manage_sounds)

        toggle_mode_action = edit_menu.addAction('타이머/스톱워치 변경')
        toggle_mode_action.triggered.connect(self.toggle_mode)

        menubar.addMenu(edit_menu)

        time_format_menu = menubar.addMenu('시간 형식')

        self.time_format_action_group = QActionGroup(self)

        mm_ss_action = QAction('mm:ss', self)
        mm_ss_action.setCheckable(True)
        mm_ss_action.triggered.connect(lambda: self.set_time_format('mm:ss'))
        self.time_format_action_group.addAction(mm_ss_action)

        hh_mm_ss_action = QAction('hh:mm:ss', self)
        hh_mm_ss_action.setCheckable(True)
        hh_mm_ss_action.triggered.connect(lambda: self.set_time_format('hh:mm:ss'))
        self.time_format_action_group.addAction(hh_mm_ss_action)

        time_format_menu.addActions(self.time_format_action_group.actions())

        menubar.addMenu(time_format_menu)

    def set_time_format(self, format):
        self.time_format = format
        if self.time_format == 'mm:ss':
            self.time_input.setDisplayFormat("mm:ss")
            self.time_input.setTime(QTime(0, 0))
        else:
            self.time_input.setDisplayFormat("HH:mm:ss")
            self.time_input.setTime(QTime(0, 0, 0))

    def manage_sounds(self):
        self.sound_manager = SoundManager(self.sounds, self)
        self.sound_manager.exec_()
        self.save_sounds()
        self.update_alarm_sounds()

    def update_alarm_sounds(self):
        self.start_alarm_input.clear()
        self.one_minute_before_input.clear()
        self.end_alarm_input.clear()
        for sound in self.sounds:
            self.start_alarm_input.addItem(sound['name'])
            self.one_minute_before_input.addItem(sound['name'])
            self.end_alarm_input.addItem(sound['name'])

    def resize_to_70_percent(self):
        desktop = QDesktopWidget().availableGeometry(self)
        screen_width = desktop.width()
        screen_height = desktop.height()
        self.setGeometry(
            int(screen_width * 0.15),
            int(screen_height * 0.15),
            int(screen_width * 0.7),
            int(screen_height * 0.7)
        )
        self.center()
        self.update_spacers()

    def center(self):
        frameGm = self.frameGeometry()
        screen = QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(screen)
        self.move(frameGm.topLeft())

    def toggle_mode(self):
        self.is_timer_mode = not self.is_timer_mode
        if self.is_timer_mode:
            self.setWindowTitle('카운트다운 타이머 알람')
            self.start_button.setText('타이머 시작하기')
        else:
            self.setWindowTitle('스톱워치 타이머 알람')
            self.start_button.setText('스톱워치 시작하기')

    def start_timer(self):
        if self.is_timer_mode:
            total_time = self.time_input.text()
            self.time_left = self.time_to_seconds(total_time)
            self.saved_time = total_time  # 저장된 시간을 업데이트
            if self.time_left > 0:
                if not self.end_alarm_input.currentText():
                    QMessageBox.warning(self, 'Error', '끝나는 시간의 알람음을 선택 해 주세요.')
                    return
                self.timer.start(1000)
                self.update_timer_label()
                self.play_sound(self.start_alarm_input.currentText())  # 시작 알람 울리기
        else:
            self.elapsed_timer.start()
            self.timer.start(1000)

    def stop_timer(self):
        self.timer.stop()
        self.enable_alarm_inputs()  # 알람 입력 활성화

    def reset_timer(self):
        self.time_input.setTime(QTime(0, 0) if self.time_format == 'mm:ss' else QTime(0, 0, 0))
        self.stop_timer()

    def update_timer(self):
        if self.is_timer_mode:
            if self.time_left > 0:
                self.time_left -= 1
                self.update_timer_label()
                self.check_alarms()
            else:
                self.timer.stop()
                self.enable_alarm_inputs()  # 타이머가 종료되면 알람 입력 활성화
                # self.alert('시간이 종료되었습니다!')
        else:
            elapsed = self.elapsed_timer.elapsed() // 1000
            self.time_input.setTime(QTime(0, 0).addSecs(elapsed))
            self.check_alarms()

    def update_timer_label(self):
        time_str = self.seconds_to_time(self.time_left)
        self.time_input.setTime(QTime.fromString(time_str, "HH:mm:ss"))

    def check_alarms(self):
        if self.is_timer_mode:
            if self.time_left == 60:  # 1분 전
                self.play_sound(self.one_minute_before_input.currentText())
            elif self.time_left == 0:  # 타이머 종료
                self.play_sound(self.end_alarm_input.currentText())
        else:
            elapsed = self.elapsed_timer.elapsed() // 1000
            if elapsed % 60 == 0 and elapsed != 0:  # 1분마다
                self.play_sound(self.one_minute_before_input.currentText())
            elif elapsed == 0:  # 스톱워치 종료
                self.play_sound(self.end_alarm_input.currentText())

    def get_sound_path(self, sound_name):
        sound = next((sound for sound in self.sounds if sound['name'] == sound_name), None)
        if sound:
            return sound['file']
        return None

    def play_sound(self, sound_name):
        sound_path = self.get_sound_path(sound_name)
        if sound_path:
            try:
                print(f"Playing sound: {sound_path}")
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()  # 현재 재생 중인 소리를 멈추고 새 소리를 재생
                pygame.mixer.music.load(sound_path)
                pygame.mixer.music.play()
            except pygame.error as e:
                print(f"Error playing sound: {e}")
        else:
            print(f"Sound not found for name: {sound_name}")


    def alert(self, message):
        QMessageBox.information(self, 'Alert', message)

    def time_to_seconds(self, time_str):
        parts = time_str.split(':')
        if len(parts) == 2:
            m, s = map(int, parts)
            return m * 60 + s
        elif len(parts) == 3:
            h, m, s = map(int, parts)
            return h * 3600 + m * 60 + s
        else:
            raise ValueError("Invalid time format")

    def seconds_to_time(self, seconds):
        h, remainder = divmod(seconds, 3600)
        m, s = divmod(remainder, 60)
        return f'{h:02}:{m:02}:{s:02}'

    def is_valid_time_format(self, time_str):
        try:
            h, m, s = map(int, time_str.split(':'))
            return True
        except:
            return False

    def disable_alarm_inputs(self):
        self.start_alarm_input.setEnabled(False)
        self.one_minute_before_input.setEnabled(False)
        self.end_alarm_input.setEnabled(False)

    def enable_alarm_inputs(self):
        self.start_alarm_input.setEnabled(True)
        self.one_minute_before_input.setEnabled(True)
        self.end_alarm_input.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    app.exec_()
