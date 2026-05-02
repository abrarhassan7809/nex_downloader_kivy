# -*- mode: python ; coding: utf-8 -*-
from kivymd import hooks_path as kivymd_hooks_path
from kivy_deps import sdl2, glew

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('nex.kv', '.'), ('assets', 'assets')],
    hiddenimports=[
        'kivymd.icon_definitions',
        'kivymd.stiffscroll',
        'plyer.platforms.win.notification',
        'yt_dlp',
        'ffpyplayer'
    ],
    hookspath=[kivymd_hooks_path],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Kivy aur KivyMD ki files add karne ke liye
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,

    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)], # Ye Windows dependencies ke liye hai
    name='NexDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # Black window nahi aayegi
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/nexdownloader-icon.ico'
)