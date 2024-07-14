import sys
import threading
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTimeEdit, QComboBox, QListWidget, QListWidgetItem, QMessageBox, QDesktopWidget,
                             QSpacerItem, QSizePolicy, QMenuBar, QColorDialog, QLineEdit, QFileDialog, QInputDialog,
                             QDialog)
from PyQt5.QtCore import QTimer, Qt, QTime, QElapsedTimer
import pygame


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        pygame.mixer.init()  # Initialize the mixer module for pygame
        self.stopped_background_color = 'red'
        self.running_background_color = 'green'
        self.current_background_color = self.stopped_background_color
        self.sounds = []
        self.sounds_file = "sounds.json"
        self.default_sounds_folder = "sounds"
        self.is_timer_mode = True
        self.load_sounds()
        self.initUI()

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
        self.timer_container.setStyleSheet(f"background-color: {self.current_background_color};")
        self.timer_container_layout = QVBoxLayout(self.timer_container)

        self.time_input = QTimeEdit(QTime(0, 0, 0), self.timer_container)
        self.time_input.setAlignment(Qt.AlignCenter)
        self.time_input.setDisplayFormat("HH:mm:ss")
        self.time_input.setStyleSheet("font-size: 100px; height: 100px;")
        self.time_input.setFixedHeight(100)  # Fix the height to 100px

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

        alarm_time_label = QLabel('알람 종료 전 시간 (HH:mm:ss):', self)
        alarm_time_label.setStyleSheet("font-size: 20px;")
        self.alarm_layout.addWidget(alarm_time_label)

        self.alarm_time_input = QTimeEdit(QTime(0, 0, 0), self)
        self.alarm_time_input.setDisplayFormat("HH:mm:ss")
        self.alarm_time_input.setStyleSheet("font-size: 20px;")
        self.alarm_layout.addWidget(self.alarm_time_input)

        self.alarm_sound_input = QComboBox(self)
        self.alarm_sound_input.setStyleSheet("font-size: 20px;")
        self.update_alarm_sounds()
        self.alarm_layout.addWidget(self.alarm_sound_input)

        self.add_alarm_button = QPushButton('알람 추가', self)
        self.add_alarm_button.setStyleSheet("font-size: 20px;")
        self.add_alarm_button.clicked.connect(self.add_alarm)
        self.alarm_layout.addWidget(self.add_alarm_button)

        self.main_layout.addLayout(self.alarm_layout)

        self.alarm_list = QListWidget(self)
        self.alarm_list.setStyleSheet("font-size: 20px;")
        self.alarm_list.itemDoubleClicked.connect(self.remove_alarm)
        self.main_layout.addWidget(self.alarm_list)

        self.setWindowTitle('카운트다운 알람')
        self.resize_to_70_percent()
        self.create_menu()
        self.update_background_color(self.current_background_color)
        self.show()

        self.time_left = 0
        self.alarms = []

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

        edit_menu = menubar.addMenu('Edit')

        change_stopped_bg_action = edit_menu.addAction('멈춤 상태 배경 색상 변경')
        change_stopped_bg_action.triggered.connect(self.change_stopped_background_color)

        change_running_bg_action = edit_menu.addAction('실행 상태 배경 색상 변경')
        change_running_bg_action.triggered.connect(self.change_running_background_color)

        manage_sounds_action = edit_menu.addAction('음원 설정')
        manage_sounds_action.triggered.connect(self.manage_sounds)

        toggle_mode_action = edit_menu.addAction('타이머/스톱워치 변경')
        toggle_mode_action.triggered.connect(self.toggle_mode)

    def change_stopped_background_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.stopped_background_color = color.name()
            if not self.timer.isActive():
                self.update_background_color(self.stopped_background_color)

    def change_running_background_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.running_background_color = color.name()
            if self.timer.isActive():
                self.update_background_color(self.running_background_color)

    def manage_sounds(self):
        self.sound_manager = SoundManager(self.sounds, self)
        self.sound_manager.exec_()
        self.save_sounds()
        self.update_alarm_sounds()

    def update_alarm_sounds(self):
        self.alarm_sound_input.clear()
        for sound in self.sounds:
            self.alarm_sound_input.addItem(sound['name'])

    def update_background_color(self, color):
        self.current_background_color = color
        self.timer_container.setStyleSheet(f"background-color: {color}")

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
        if self.is_timer_mode:
            total_time = self.time_input.time().toString("HH:mm:ss")
            self.time_left = self.time_to_seconds(total_time)
            if self.time_left > 0:
                if not any(alarm[0] == 0 for alarm in self.alarms):
                    QMessageBox.warning(self, 'Error', '끝나는 시간의 알람음을 선택 해 주세요.')
                    return
                self.timer.start(1000)
                self.update_background_color(self.running_background_color)
                self.update_timer_label()
        else:
            self.elapsed_timer.start()
            self.timer.start(1000)
            self.update_background_color(self.running_background_color)

    def stop_timer(self):
        self.timer.stop()
        self.update_background_color(self.stopped_background_color)

    def update_timer(self):
        if self.is_timer_mode:
            if self.time_left > 0:
                self.time_left -= 1
                self.update_timer_label()
                self.check_alarms()
            else:
                self.timer.stop()
                self.update_background_color(self.stopped_background_color)
                self.alert('시간이 종료되었습니다!')
                if not any(alarm[0] == 0 for alarm in self.alarms):
                    QMessageBox.warning(self, 'Error', '끝나는 시간의 알람을 선택 해 주세요')
        else:
            elapsed = self.elapsed_timer.elapsed() // 1000
            self.time_input.setTime(QTime(0, 0).addSecs(elapsed))
            self.check_alarms()

    def update_timer_label(self):
        time_str = self.seconds_to_time(self.time_left)
        self.time_input.setTime(QTime.fromString(time_str, "HH:mm:ss"))

    def add_alarm(self):
        alarm_time = self.alarm_time_input.time().toString("HH:mm:ss")
        sound_name = self.alarm_sound_input.currentText()
        sound_path = next((sound['file'] for sound in self.sounds if sound['name'] == sound_name), None)
        if self.is_valid_time_format(alarm_time) and sound_path:
            alarm_seconds = self.time_to_seconds(alarm_time)
            self.alarms.append((alarm_seconds, sound_path))
            alarm_item = QListWidgetItem(f'끝나는 시간: {alarm_time}, 음원: {sound_name}')
            alarm_item.setData(Qt.UserRole, (alarm_seconds, sound_path))
            self.alarm_list.addItem(alarm_item)

        else:
            QMessageBox.warning(self, 'Error', '음원 파일을 제공 해 주세요.')

    def remove_alarm(self, item):
        row = self.alarm_list.row(item)
        self.alarm_list.takeItem(row)
        self.alarms.pop(row)

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
                self.sounds.append({'이름': name, '파일': file})
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
                    self.sounds[current_row] = {'name': name, 'file': file}
                    self.update_sound_list()

    def delete_sound(self):
        current_row = self.sound_list.currentRow()
        if current_row >= 0:
            del self.sounds[current_row]
            self.update_sound_list()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    # sys.exit(app.exec_())
    ex.show()
    app.exec_()
