import sys
import threading
import json
import os
import shutil  # Importing shutil for file operations
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTimeEdit, QComboBox, QListWidget, QListWidgetItem, QMessageBox, QDesktopWidget,
                             QSpacerItem, QSizePolicy, QMenuBar, QColorDialog, QLineEdit, QFileDialog, QInputDialog,
                             QDialog, QAction, QActionGroup)
from PyQt5.QtCore import QTimer, Qt, QTime, QElapsedTimer, QStandardPaths
import pygame

def resource_path(relative_path):
    """개발 및 PyInstaller에 대해 리소스의 절대 경로를 가져옵니다."""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        pygame.mixer.init()  # Initialize the mixer module for pygame
        self.background_color = 'black'
        self.text_color = 'red'
        self.sounds = []
        self.sounds_file = os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), "sounds.json")  # Updated path
        # self.default_sounds_folder = os.path.join(os.path.dirname(__file__), "sounds")  # Default sounds folder
        self.default_sounds_folder = resource_path("sounds")
        self.user_sounds_folder = os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), "user_sounds")  # User sounds folder
        self.is_timer_mode = True
        self.setup_sound_folders()  # Set up sound folders
        self.load_sounds()
        self.time_format = 'mm:ss'
        self.initUI()

    def setup_sound_folders(self):
        if not os.path.exists(self.user_sounds_folder):
            os.makedirs(self.user_sounds_folder)

    def load_sounds(self):
        # Load existing sounds from JSON file
        if os.path.exists(self.sounds_file):
            with open(self.sounds_file, 'r') as f:
                self.sounds = json.load(f)
        else:
            self.sounds = []

        # Load default sounds from the default sounds folder
        if os.path.exists(self.default_sounds_folder):
            for file_name in os.listdir(self.default_sounds_folder):
                if file_name.endswith(('.mp3', '.wav')):
                    sound_name = os.path.splitext(file_name)[0]
                    sound_file_path = os.path.join(self.default_sounds_folder, file_name)
                    if not any(sound['file'] == sound_file_path for sound in self.sounds):
                        self.sounds.append({'name': sound_name, 'file': sound_file_path})

        self.save_sounds()

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

        # Create the timer container with the specified background color
        self.timer_container = QWidget(self.centralWidget)
        self.timer_container_layout = QVBoxLayout(self.timer_container)

        self.time_input = QTimeEdit(QTime(0, 0, 0), self.timer_container)
        self.time_input.setAlignment(Qt.AlignCenter)
        self.time_input.setDisplayFormat("HH:mm:ss")
        self.time_input.setStyleSheet("font-size: 300px; height: 300px; background-color: black; color: red;")
        self.time_input.setFixedHeight(300)  # Fix the height to 100px
        self.set_time_format(self.time_format)

        # Add the time input to the timer container layout and center it
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

        self.update_alarm_sounds()  # Populate the alarm sounds combo boxes

        self.alarm_list = QListWidget(self)
        self.alarm_list.setStyleSheet("font-size: 20px;")
        self.alarm_list.itemDoubleClicked.connect(self.remove_alarm)
        self.main_layout.addWidget(self.alarm_list)

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
        # Remove old spacers if they exist
        if hasattr(self, 'top_spacer'):
            self.timer_container_layout.removeItem(self.top_spacer)
        if hasattr(self, 'bottom_spacer'):
            self.timer_container_layout.removeItem(self.bottom_spacer)

        desktop = QDesktopWidget().availableGeometry(self)
        screen_height = desktop.height()

        # Calculate new spacer heights
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
            int(screen_width * 0.15),  # x position
            int(screen_height * 0.15),  # y position
            int(screen_width * 0.7),  # width
            int(screen_height * 0.7)  # height
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
        start_alarm_sound = next((sound['file'] for sound in self.sounds if sound['name'] == self.start_alarm_input.currentText()), None)
        one_minute_before_sound = next((sound['file'] for sound in self.sounds if sound['name'] == self.one_minute_before_input.currentText()), None)
        end_alarm_sound = next((sound['file'] for sound in self.sounds if sound['name'] == self.end_alarm_input.currentText()), None)

        self.alarms = []
        if start_alarm_sound:
            self.alarms.append((0, start_alarm_sound))  # Trigger at the start
        if one_minute_before_sound:
            one_minute_before_time = self.time_to_seconds(self.time_input.time().toString("HH:mm:ss")) - 60
            self.alarms.append((one_minute_before_time, one_minute_before_sound))  # Trigger one minute before the end
        if end_alarm_sound:
            end_time = self.time_to_seconds(self.time_input.time().toString("HH:mm:ss"))
            self.alarms.append((end_time, end_alarm_sound))  # Trigger at the end

        if self.is_timer_mode:
            total_time = self.time_input.time().toString("HH:mm:ss")
            self.time_left = self.time_to_seconds(total_time)
            if self.time_left > 0:
                self.timer.start(1000)
                self.update_timer_label()
        else:
            self.elapsed_timer.start()
            self.timer.start(1000)

    def stop_timer(self):
        self.timer.stop()

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
                self.alert('시간이 종료되었습니다!')
        else:
            elapsed = self.elapsed_timer.elapsed() // 1000
            self.time_input.setTime(QTime(0, 0).addSecs(elapsed))
            self.check_alarms()

    def update_timer_label(self):
        time_str = self.seconds_to_time(self.time_left)
        self.time_input.setTime(QTime.fromString(time_str, "HH:mm:ss"))

    def check_alarms(self):
        for alarm_time, sound_path in self.alarms:
            if (self.is_timer_mode and self.time_left == alarm_time) or (
                    not self.is_timer_mode and self.elapsed_timer.elapsed() // 1000 == alarm_time):
                threading.Thread(target=self.play_sound, args=(sound_path,)).start()

    def play_sound(self, sound_path):
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play()

    def alert(self, message):
        QMessageBox.information(self, 'Alert', message)

    def time_to_seconds(self, time_str):
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s

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

    def remove_alarm(self, item):
        row = self.alarm_list.row(item)
        self.alarm_list.takeItem(row)
        self.alarms.pop(row)


class SoundManager(QDialog):
    def __init__(self, sounds, parent=None):
        super().__init__(parent)
        self.sounds = sounds
        self.setWindowTitle('사운드 메니저')
        self.setGeometry(100, 100, 600, 400)
        self.setLayout(QVBoxLayout())

        self.sound_list = QListWidget(self)
        self.sound_list.setStyleSheet("font-size: 20px;")
        self.update_sound_list()
        self.layout().addWidget(self.sound_list)

        self.control_layout = QHBoxLayout()

        self.add_button = QPushButton('음원 추가하기', self)
        self.add_button.clicked.connect(self.add_sound)
        self.control_layout.addWidget(self.add_button)

        self.edit_button = QPushButton('음원 편집하기', self)
        self.edit_button.clicked.connect(self.edit_sound)
        self.control_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton('음원 삭제하기', self)
        self.delete_button.clicked.connect(self.delete_sound)
        self.control_layout.addWidget(self.delete_button)

        self.layout().addLayout(self.control_layout)

    def update_sound_list(self):
        self.sound_list.clear()
        for sound in self.sounds:
            self.sound_list.addItem(f"이름: {sound['name']}, 파일: {sound['file']}")

    def add_sound(self):
        name, ok = QInputDialog.getText(self, '음원 이름', '입력된 음원 이름:')
        if ok and name:
            file, _ = QFileDialog.getOpenFileName(self, '음원 파일 열기', '', '음원 파일 (*.mp3 *.wav)')
            if file:
                destination = os.path.join(self.parent().user_sounds_folder, os.path.basename(file))
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                if not os.path.exists(destination):
                    shutil.copy(file, destination)
                self.sounds.append({'name': name, 'file': destination})
                self.update_sound_list()

    def edit_sound(self):
        current_row = self.sound_list.currentRow()
        if current_row >= 0:
            current_sound = self.sounds[current_row]
            name, ok = QInputDialog.getText(self, '음원파일 이름 변경', '새로운 음원파일 이름:',
                                            text=current_sound['name'])
            if ok and name:
                file, _ = QFileDialog.getOpenFileName(self, '음원파일 열기', '', '음원파일 (*.mp3 *.wav)')
                if file:
                    destination = os.path.join(self.parent().user_sounds_folder, os.path.basename(file))
                    os.makedirs(os.path.dirname(destination), exist_ok=True)
                    if not os.path.exists(destination):
                        shutil.copy(file, destination)
                    self.sounds[current_row] = {'name': name, 'file': destination}
                    self.update_sound_list()

    def delete_sound(self):
        current_row = self.sound_list.currentRow()
        if current_row >= 0:
            del self.sounds[current_row]
            self.update_sound_list()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    app.exec_()
