from kivy.utils import platform
from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import StringProperty, ColorProperty, NumericProperty
from plyer import notification
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.card import MDCard
from kivy.core.window import Window
import os
import threading
import ssl
import socket
import uuid
import sys
import yt_dlp


# SSL Fix
ssl._create_default_https_context = ssl._create_unverified_context
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from jnius import autoclass

if platform != 'android':
    Window.size = (400, 700)


class MyLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(f"YT-DLP Error: {msg}")


KV = """
<DownloadTaskCard>:
    orientation: "vertical"
    size_hint_y: None
    height: "140dp"
    padding: "15dp"
    radius: [20,]
    md_bg_color: app.card_color
    elevation: 2
    spacing: "8dp"

    MDBoxLayout:
        size_hint_y: None
        height: "30dp"
        MDLabel:
            text: root.title
            bold: True
            theme_text_color: "Custom"
            text_color: app.text_color
            shorten: True
            shorten_from: 'right'

        MDIconButton:
            icon: "pause-circle" if root.is_running else "play-circle"
            theme_icon_color: "Custom"
            icon_color: [0.91, 0.27, 0.37, 1]
            on_release: app.toggle_task(root.task_id)

        MDIconButton:
            icon: "close-circle"
            theme_icon_color: "Custom"
            icon_color: [0.5, 0.5, 0.5, 1]
            on_release: app.cancel_task(root.task_id)

    MDProgressBar:
        value: root.progress
        color: [0.91, 0.27, 0.37, 1]
        height: "8dp"

    MDBoxLayout:
        MDLabel:
            text: root.status
            font_style: "Caption"
            theme_text_color: "Secondary"
        MDLabel:
            text: f"{int(root.progress)}%"
            halign: "right"
            theme_text_color: "Custom"
            text_color: app.text_color

MDScreen:
    md_bg_color: app.bg_color

    MDBoxLayout:
        orientation: 'vertical'
        padding: "15dp"
        spacing: "10dp"

        # Header
        MDBoxLayout:
            size_hint_y: None
            height: "60dp"
            MDLabel:
                text: "Nex Multi-Downloader"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: [0.91, 0.27, 0.37, 1]
            MDIconButton:
                icon: "brightness-6"
                theme_icon_color: "Custom"
                icon_color: app.text_color
                on_release: app.toggle_theme()

        # Input Box
        MDCard:
            orientation: "vertical"
            padding: "15dp"
            radius: [20,]
            md_bg_color: app.card_color
            size_hint_y: None
            height: "160dp"
            spacing: "10dp"

            MDBoxLayout:
                spacing: "5dp"
                MDTextField:
                    id: url_input
                    hint_text: "Paste YouTube Link"
                    mode: "fill"
                    fill_color_normal: app.input_bg
                    text_color_normal: app.text_color
                    hint_text_color_normal: [0.5, 0.5, 0.5, 1]
                MDIconButton:
                    icon: "plus-circle"
                    icon_size: "35dp"
                    theme_icon_color: "Custom"
                    icon_color: [0.91, 0.27, 0.37, 1]
                    on_release: app.add_to_queue()

            MDBoxLayout:
                spacing: "10dp"
                MDRaisedButton:
                    id: type_btn
                    text: "Video"
                    size_hint_x: 1
                    md_bg_color: app.btn_secondary
                    on_release: app.type_menu.open()
                MDRaisedButton:
                    id: qual_btn
                    text: "720p"
                    size_hint_x: 1
                    md_bg_color: app.btn_secondary
                    on_release: app.quality_menu.open()

        # Tasks List
        MDScrollView:
            MDBoxLayout:
                id: task_list
                orientation: "vertical"
                adaptive_height: True
                padding: "5dp"
                spacing: "12dp"
"""


class DownloadTaskCard(MDCard):
    task_id = StringProperty()
    title = StringProperty("Fetching...")
    status = StringProperty("Pending...")
    progress = NumericProperty(0)
    is_running = NumericProperty(1)  # 1 for running, 0 for paused


class NexDownloaderApp(MDApp):
    bg_color = ColorProperty([0.05, 0.05, 0.05, 1])
    card_color = ColorProperty([0.12, 0.12, 0.12, 1])
    text_color = ColorProperty([1, 1, 1, 1])
    input_bg = ColorProperty([0.15, 0.15, 0.15, 1])
    btn_secondary = ColorProperty([0.2, 0.2, 0.2, 1])

    active_tasks = {}

    def build(self):
        self.title = "Nex Multi-Downloader"
        self.theme_cls.theme_style = "Dark"
        return Builder.load_string(KV)

    def on_start(self):
        self.setup_menus()
        if platform == 'android':
            request_permissions(
                [Permission.INTERNET, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

    def setup_menus(self):
        t_items = [{"text": i, "viewclass": "OneLineListItem", "on_release": lambda x=i: self.set_type(x)} for i in
                   ["Video", "Audio"]]
        self.type_menu = MDDropdownMenu(caller=self.root.ids.type_btn, items=t_items, width_mult=3)
        q_items = [{"text": i, "viewclass": "OneLineListItem", "on_release": lambda x=i: self.set_quality(x)} for i in
                   ["360p", "480p", "720p", "1080p"]]
        self.quality_menu = MDDropdownMenu(caller=self.root.ids.qual_btn, items=q_items, width_mult=3)

    def set_type(self, val):
        self.root.ids.type_btn.text = val
        self.type_menu.dismiss()

    def set_quality(self, val):
        self.root.ids.qual_btn.text = val
        self.quality_menu.dismiss()

    def add_to_queue(self):
        url = self.root.ids.url_input.text.strip()
        if not url: return

        task_id = str(uuid.uuid4())
        new_card = DownloadTaskCard(task_id=task_id)
        self.root.ids.task_list.add_widget(new_card)
        self.root.ids.url_input.text = ""

        self.active_tasks[task_id] = {"cancel": False, "paused": False, "card": new_card, "url": url}
        self.start_download_thread(task_id)

    def start_download_thread(self, task_id):
        task = self.active_tasks[task_id]
        threading.Thread(target=self.download_engine, args=(task['url'], task_id), daemon=True).start()

    def download_engine(self, url, task_id):
        path = self.get_path()
        os.makedirs(path, exist_ok=True)

        def hook(d):
            # Task check safe tarike se
            task = self.active_tasks.get(task_id)
            if not task or task.get("cancel") or task.get("paused"):
                # Agar pause ya cancel ho, toh thread ko terminate kar den
                raise Exception("STOPPED_BY_USER")

            if d['status'] == 'downloading':
                p = d.get('downloaded_bytes', 0)
                t = d.get('total_bytes') or d.get('total_bytes_estimate')
                if t:
                    self.update_card(task_id, (p / t) * 100, "Downloading...")

        opts = {
            'outtmpl': f'{path}/%(title)s.%(ext)s',
            'progress_hooks': [hook],
            'logger': MyLogger(),
            'quiet': True,
            'continuedl': True,  # Resume ke liye zaroori hai
            'nocheckcertificate': True,
        }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Video')
                self.update_card(task_id, 100, "Finished!", title=title)
                self.send_platform_notification("Download Complete", f"Saved: {title}")
        except Exception as e:
            # Safe checking taake KeyError na aaye
            if task_id in self.active_tasks:
                if "STOPPED_BY_USER" in str(e):
                    # Card ko delete nahi karna, bas status update karna hai
                    self.update_card(task_id, self.active_tasks[task_id]["card"].progress, "Paused")
                else:
                    print(f"Error: {e}")
                    self.update_card(task_id, 0, "Error / Timeout")

    def toggle_task(self, tid):
        if tid in self.active_tasks:
            task = self.active_tasks[tid]
            if task["paused"]:
                # RESUME Logic: Naya thread shuru karen
                task["paused"] = False
                task["card"].is_running = 1
                task["card"].status = "Resuming..."
                threading.Thread(target=self.download_engine, args=(task['url'], tid), daemon=True).start()
            else:
                # PAUSE Logic: Thread ko exception throw karwa kar band kar den
                task["paused"] = True
                task["card"].is_running = 0
                task["card"].status = "Pausing..."

    def cancel_task(self, tid):
        """Cancel mein card remove karna hai"""
        if tid in self.active_tasks:
            self.active_tasks[tid]["cancel"] = True
            # Foran remove na karen, pehle flag set karen taake thread ruk jaye
            card = self.active_tasks[tid]["card"]
            self.root.ids.task_list.remove_widget(card)
            # Thori dair baad dictionary se delete karen taake KeyError na aaye
            def delayed_delete(dt):
                if tid in self.active_tasks:
                    del self.active_tasks[tid]
            from kivy.clock import Clock
            Clock.schedule_once(delayed_delete, 0.5)

    @mainthread
    def update_card(self, tid, prog, stat, title=None):
        if tid in self.active_tasks:
            card = self.active_tasks[tid]["card"]
            card.progress, card.status = prog, stat
            if title: card.title = title

    def send_platform_notification(self, title, msg):
        try:
            notification.notify(title=title, message=msg, app_name="NexDownloader")
        except:
            pass

    def get_path(self):
        if platform == 'android':
            try:
                context = autoclass('org.kivy.android.PythonActivity').mActivity
                return os.path.join(context.getExternalMediaDirs()[0].getAbsolutePath(), "NexDownloads")
            except:
                return os.path.join("/sdcard/Download", "NexDownloads")
        else:
            # Windows/Linux/Mac PC path
            return os.path.join(os.path.expanduser("~"), "Downloads", "NexDownloads")

    def toggle_theme(self):
        self.theme_cls.theme_style = "Light" if self.theme_cls.theme_style == "Dark" else "Dark"
        if self.theme_cls.theme_style == "Light":
            self.bg_color, self.card_color, self.text_color = [0.95, 0.95, 0.95, 1], [1, 1, 1, 1], [0, 0, 0, 1]
            self.input_bg, self.btn_secondary = [0.9, 0.9, 0.9, 1], [0.85, 0.85, 0.85, 1]
        else:
            self.bg_color, self.card_color, self.text_color = [0.05, 0.05, 0.05, 1], [0.12, 0.12, 0.12, 1], [1, 1, 1, 1]
            self.input_bg, self.btn_secondary = [0.15, 0.15, 0.15, 1], [0.2, 0.2, 0.2, 1]


if __name__ == "__main__":
    NexDownloaderApp().run()