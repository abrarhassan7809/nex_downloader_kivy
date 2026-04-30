# Nex Multi-Downloader 🚀

A modern, feature-rich **multi-task video & audio downloader** built with **KivyMD** and powered by `yt-dlp`.
Designed for Android (and desktop), this app allows you to download multiple media files simultaneously with a clean UI and smooth performance.

---

## ✨ Features

* 🎬 **Video & Audio Download**

  * Download videos in multiple qualities (360p, 480p, 720p, 1080p)
  * Extract audio from videos

* 📥 **Multi-Download Queue**

  * Add multiple links and download them simultaneously

* ⏸️ **Pause / Resume**

  * Pause any download and resume later

* ❌ **Cancel Downloads**

  * Instantly stop and remove tasks safely

* 📊 **Live Progress Tracking**

  * Real-time progress bar and status updates

* 🔔 **Notifications**

  * Get notified when downloads are complete

* 🎨 **Modern UI**

  * Built with KivyMD (Material Design)
  * Dark / Light theme toggle

* 📁 **Smart Storage Handling**

  * Works with Android scoped storage (no crashes)
  * Automatic folder creation

---

## 📱 Platform Support

* ✅ Android (Primary target)
* ✅ Windows / Linux / macOS (for testing & development)

---

## 🛠️ Built With

* [Kivy](https://kivy.org/)
* [KivyMD](https://kivymd.readthedocs.io/)
* [yt-dlp](https://github.com/yt-dlp/yt-dlp)
* [Plyer](https://github.com/kivy/plyer)

---

## ⚙️ Installation (Development)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/nex-downloader.git
cd nex-downloader
```

### 2. Install Dependencies

```bash
pip install kivy kivymd yt-dlp plyer pyjnius requests
```

### 3. Run the App

```bash
python main.py
```

---

## 📦 Build APK (Android)

Make sure you have **Buildozer** installed:

```bash
buildozer android debug
```

---

## ⚠️ Notes

* Some formats may require **FFmpeg** for proper audio conversion.
* Download speed depends on your internet connection.
* Android storage access follows **Scoped Storage rules**.

---

## 📂 Default Download Location

* **Android:**
  `/storage/emulated/0/Android/media/<package_name>/NexDownloads`

* **Desktop:**
  `~/Downloads/NexDownloads`
  * Run this command in terminal for build software:
  `pyinstaller --clean NexDownloader.spec`

---

## 🚧 Future Improvements

* 🎬 Thumbnail preview before download
* 🎵 Full MP3 conversion with FFmpeg
* 📂 Open/download folder button
* 📜 Download history
* 🌐 Support for more platforms (TikTok, Facebook, etc.)

---

## 🤝 Contributing

Contributions are welcome!
Feel free to fork this repository and submit a pull request.

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

Developed by **OneCodeTechSolution**

---

## ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub!
