from kivy.uix.boxlayout import BoxLayout
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform
from kivy.clock import mainthread, Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, ColorProperty, NumericProperty
from plyer import notification
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.card import MDCard
from kivy.core.window import Window
from kivy.uix.popup import Popup
import os
import sys
import threading
import ssl
import uuid
import yt_dlp


os.environ['KIVY_VIDEO'] = 'ffpyplayer'
# SSL Fix
ssl._create_default_https_context = ssl._create_unverified_context
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from jnius import autoclass
else:
    Window.size = (400, 700)


class MyLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(f"YT-DLP Error: {msg}")


class DownloadTaskCard(MDCard):
    task_id = StringProperty()
    title = StringProperty("Fetching...")
    status = StringProperty("Pending...")
    progress = NumericProperty(0)
    is_running = NumericProperty(1)  # 1 = Running, 0 = Paused


class LibraryItemCard(MDCard):
    title = StringProperty("")
    file_path = StringProperty("")


class VideoPlayerWidget(BoxLayout):
    source = StringProperty("")
    duration = NumericProperty(1)
    position = NumericProperty(0)
    current_time = StringProperty("00:00")
    total_time = StringProperty("00:00")
    volume = NumericProperty(0.5)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update_ev = Clock.schedule_interval(self.update_progress, 0.5)

    def update_progress(self, dt):
        v = self.ids.video_instance
        if v.duration > 1:
            self.duration = v.duration
            self.total_time = self.format_time(v.duration)
        if v.position >= 0:
            self.position = v.position
            self.current_time = self.format_time(v.position)

    def format_time(self, seconds):
        m, s = divmod(int(max(0, seconds)), 60)
        return f"{m:02d}:{s:02d}"

    def toggle_play(self):
        v = self.ids.video_instance
        v.state = 'pause' if v.state == 'play' else 'play'

    def seek_video(self, value):
        v = self.ids.video_instance
        if v.duration > 0:
            v.seek(value / v.duration)

    def set_volume(self, ui_val):
        self.volume = ui_val / 100
        self.ids.video_instance.volume = self.volume

    def cleanup(self):
        Clock.unschedule(self._update_ev)
        self.ids.video_instance.state = 'stop'
        self.ids.video_instance.unload()


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class NexDownloaderApp(MDApp):
    accent_color = ColorProperty([0.91, 0.27, 0.37, 1])
    bg_dark = ColorProperty([0.02, 0.02, 0.03, 1])
    card_light = ColorProperty([0.1, 0.1, 0.12, 1])
    text_main = ColorProperty([1, 1, 1, 1])

    active_tasks = {}

    def build(self):
        self.title = "Nex Multi-Downloader"
        settings_path = os.path.join(self.user_data_dir, 'settings.json')
        self.store = JsonStore(settings_path)

        if self.store.exists('theme'):
            saved_style = self.store.get('theme')['style']
            self.theme_cls.theme_style = saved_style
        else:
            self.theme_cls.theme_style = "Dark"

        self.apply_theme_colors(self.theme_cls.theme_style)
        kv_file = resource_path('nex.kv')
        return Builder.load_file(kv_file)

    def toggle_theme(self):
        new_style = "Light" if self.theme_cls.theme_style == "Dark" else "Dark"
        self.theme_cls.theme_style = new_style
        self.apply_theme_colors(new_style)
        # Setting save karen
        self.store.put('theme', style=new_style)

    def apply_theme_colors(self, style):
        if style == "Light":
            self.bg_dark = [0.94, 0.94, 0.96, 1]
            self.card_light = [0.98, 0.98, 1, 1]
            self.text_main = [0.12, 0.12, 0.15, 1]
        else:
            self.bg_dark = [0.02, 0.02, 0.03, 1]
            self.card_light = [0.1, 0.1, 0.12, 1]
            self.text_main = [1, 1, 1, 1]

    def on_start(self):
        self.setup_menus()
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            def callback(permissions, results):
                if all(results):
                    print("All permissions granted")
                else:
                    print("Permissions denied")

            request_permissions([
                Permission.INTERNET,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ], callback)
        self.load_library()

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

    def load_library(self):
        self.root.ids.library_list.clear_widgets()
        path = self.get_path()
        if os.path.exists(path):
            files = [f for f in os.listdir(path) if f.endswith(('.mp4', '.mp3', '.mkv'))]
            for f in files:
                self.root.ids.library_list.add_widget(LibraryItemCard(title=f, file_path=os.path.join(path, f)))

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
        download_type = self.root.ids.type_btn.text
        quality = self.root.ids.qual_btn.text.replace("p", "")

        def hook(d):
            task = self.active_tasks.get(task_id)
            if not task or task["cancel"] or task["paused"]:
                raise Exception("STOPPED_BY_USER")

            if d['status'] == 'downloading':
                p = d.get('downloaded_bytes', 0)
                t = d.get('total_bytes') or d.get('total_bytes_estimate')
                if t: self.update_card(task_id, (p / t) * 100, "Downloading...")

        opts = {
            'outtmpl': f'{path}/%(title).50s.%(ext)s',
            'restrictfilenames': True,
            'format': 'best[ext=mp4]/best',
            'progress_hooks': [hook],
            'logger': MyLogger(),
            'quiet': True,
            'continuedl': True,
            'nocheckcertificate': True,
            'noplaylist': True,
        }

        # opts['format'] wali line ko is se badal den
        if download_type == "Audio":
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            })
        else:
            opts['format'] = 'best[ext=mp4]/best'

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                title = info_dict.get('title', 'Unknown Video')
                self.update_card(task_id, 0, "Fetching...", title=title)

                info = ydl.extract_info(url, download=True)
                f_name = ydl.prepare_filename(info)
                if download_type == "Audio": f_name = f_name.rsplit('.', 1)[0] + ".mp3"

                self.update_card(task_id, 100, "Download Complete", title=title)
                notification.notify(title="Success", message=title)
                Clock.schedule_once(lambda dt: self.load_library())
        except Exception as e:
            if task_id in self.active_tasks:
                if "STOPPED_BY_USER" in str(e):
                    self.update_card(task_id, self.active_tasks[task_id]["card"].progress, "Paused")
                else:
                    self.update_card(task_id, 0, "Error: Timeout/Network")

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
        if tid in self.active_tasks:
            self.active_tasks[tid]["cancel"] = True
            card = self.active_tasks[tid]["card"]
            self.root.ids.task_list.remove_widget(card)
            Clock.schedule_once(lambda dt: self.active_tasks.pop(tid, None), 0.5)

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

    def play_video(self, path):
        if not os.path.exists(path): return
        player = VideoPlayerWidget(source=path)
        self.video_popup = Popup(title="", content=player, size_hint=(1, 1), background_color=[0, 0, 0, 1],
                                 separator_height=0)
        self.video_popup.bind(on_dismiss=lambda x: player.cleanup())
        self.video_popup.open()


if __name__ == "__main__":
    NexDownloaderApp().run()