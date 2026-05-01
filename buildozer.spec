[app]
title = Nex Multi-Downloader
package.name = nexdownloader
package.domain = org.nextech
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.01

# Requirements - REMOVED extra packages jo issue create kar rahe the
requirements = python3, kivy==2.3.0, kivymd==1.2.0, yt-dlp, requests, android, plyer, pyjnius, certifi, urllib3, idna, charset-normalizer, ffmpeg, ffpyplayer

orientation = portrait

# Only essential permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, POST_NOTIFICATIONS, MANAGE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.target_sdk = 33

android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.logcat_filters = *:S python:D
android.copy_libs = 1

# Add this for yt-dlp to work properly
android.add_openssl = True
android.add_sqlite = True