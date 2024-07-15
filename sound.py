import shutil
import os
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QFileDialog, QDialog, QInputDialog)

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
            name, ok = QInputDialog.getText(self, '음원파일 이름 변경', '새로운 음원파일 이름:', text=current_sound['name'])
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