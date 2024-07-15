# -*- mode: python ; coding: utf-8 -*-

import os
import glob
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

app_data_location = os.path.expanduser("~\\AppData\\Local\\MyTimerApp")
sounds_json_path = os.path.join(app_data_location, 'sounds.json')
user_sounds_path = os.path.join(app_data_location, 'user_sounds')

# 경로가 존재하지 않으면 생성
if not os.path.exists(app_data_location):
    os.makedirs(app_data_location)
if not os.path.exists(sounds_json_path):
    open(sounds_json_path, 'w').close()
if not os.path.exists(user_sounds_path):
    os.makedirs(user_sounds_path)

# user_sounds 폴더 내의 모든 파일을 포함
user_sounds_files = [(f, os.path.join('AppData', 'user_sounds', os.path.basename(f))) for f in glob.glob(os.path.join(user_sounds_path, '*'))]

a = Analysis(
    ['main.py'],  # 실제 스크립트 파일 이름으로 변경
    pathex=['.'],
    binaries=[],
    datas=[
        (sounds_json_path, 'AppData/sounds.json'),
    ] + user_sounds_files,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='my_timer_app',  # 실제 스크립트 이름으로 변경
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='my_timer_app',  # 실제 스크립트 이름으로 변경
)
