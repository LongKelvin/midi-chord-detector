# pyinstaller/midi_chord_app.spec

# PyInstaller spec file for MIDI Chord Detector App

from PyInstaller.utils.hooks import collect_data_files
import os
import sys

block_cipher = None

app_path = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..'))
main_script = os.path.join(app_path, 'midi_chord_app.py')  

# Bundle chord definitions JSON file
datas = [
    (os.path.join(app_path, 'data', 'chord_definitions.json'), 'data')
]

a = Analysis(
    [main_script],
    pathex=[app_path],
    binaries=[],
    datas=datas,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    hiddenimports=['mido.backends.rtmidi']
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='midi_chord_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # set to True if you want a terminal window
    icon=None       # add .ico path here if you want an icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='midi_chord_app'
)
