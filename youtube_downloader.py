import os
import re
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import yt_dlp


def normalize_url(url: str) -> str:
    """Return YouTube link stripped of unnecessary query parameters."""
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    if netloc in ("youtu.be", "www.youtu.be"):
        return urlunparse(parsed._replace(query=""))
    if netloc.endswith("youtube.com"):
        qs = [(k, v) for k, v in parse_qsl(parsed.query) if k != "si"]
        return urlunparse(parsed._replace(query=urlencode(qs)))
    return url


class YouTubeDownloader(tk.Tk):
    """Simple cross-platform YouTube downloader with GUI."""

    def __init__(self) -> None:
        super().__init__()
        self.title("YT Downloader")
        self.geometry("700x500")
        self.resizable(False, False)
        self.yt = None
        self.streams = {}

        self._build_widgets()

    # -------------------------------------------------------------
    def _build_widgets(self) -> None:
        """Create and layout all widgets."""
        # URL input
        url_frame = ttk.Frame(self)
        url_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(url_frame, text="Link YouTube:").pack(side="left")
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=60)
        url_entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(url_frame, text="Sprawdź", command=self.fetch_info).pack(side="left")
        self.info_label = ttk.Label(self, text="Wprowadź link do filmu.")
        self.info_label.pack(pady=5)

        # Download type options
        option_frame = ttk.LabelFrame(self, text="Rodzaj pobierania")
        option_frame.pack(fill="x", padx=10, pady=5)
        self.option_var = tk.StringVar(value="video")
        ttk.Radiobutton(option_frame, text="Film", variable=self.option_var,
                        value="video", command=self.on_option_change).pack(side="left", padx=5)
        ttk.Radiobutton(option_frame, text="Muzyka", variable=self.option_var,
                        value="audio", command=self.on_option_change).pack(side="left", padx=5)
        ttk.Radiobutton(option_frame, text="Film + Muzyka", variable=self.option_var,
                        value="both", command=self.on_option_change).pack(side="left", padx=5)

        # Video sound options
        video_type_frame = ttk.Frame(self)
        video_type_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(video_type_frame, text="Wideo:").pack(side="left")
        self.video_sound_var = tk.StringVar(value="sound")
        self.sound_rb = ttk.Radiobutton(video_type_frame, text="z dźwiękiem", variable=self.video_sound_var,
                                        value="sound", command=self.populate_video_qualities)
        self.sound_rb.pack(side="left", padx=5)
        self.nosound_rb = ttk.Radiobutton(video_type_frame, text="bez dźwięku", variable=self.video_sound_var,
                                          value="nosound", command=self.populate_video_qualities)
        self.nosound_rb.pack(side="left", padx=5)

        # Quality selection
        quality_frame = ttk.LabelFrame(self, text="Jakość")
        quality_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(quality_frame, text="Wideo:").grid(row=0, column=0, sticky="w")
        self.video_quality = tk.StringVar()
        self.video_box = ttk.Combobox(quality_frame, textvariable=self.video_quality, state="readonly")
        self.video_box.grid(row=0, column=1, padx=5, pady=2)
        self.video_box.bind("<<ComboboxSelected>>", lambda e: self.update_filename())
        ttk.Label(quality_frame, text="Audio:").grid(row=1, column=0, sticky="w")
        self.audio_quality = tk.StringVar()
        self.audio_box = ttk.Combobox(quality_frame, textvariable=self.audio_quality, state="readonly")
        self.audio_box.grid(row=1, column=1, padx=5, pady=2)
        self.audio_box.bind("<<ComboboxSelected>>", lambda e: self.update_filename())

        # File names
        file_frame = ttk.LabelFrame(self, text="Nazwy plików")
        file_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(file_frame, text="Plik wideo:").grid(row=0, column=0, sticky="e")
        self.video_filename = tk.StringVar()
        self.video_entry = ttk.Entry(file_frame, textvariable=self.video_filename, width=50)
        self.video_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        ttk.Label(file_frame, text="Plik audio:").grid(row=1, column=0, sticky="e")
        self.audio_filename = tk.StringVar()
        self.audio_entry = ttk.Entry(file_frame, textvariable=self.audio_filename, width=50)
        self.audio_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        # Download directory
        dir_frame = ttk.Frame(self)
        dir_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(dir_frame, text="Folder docelowy:").pack(side="left")
        self.dir_var = tk.StringVar(value=str(Path.home() / "Pobrane"))
        dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, width=50)
        dir_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(dir_frame, text="Wybierz", command=self.choose_directory).pack(side="left")

        # Progress bar
        progress_frame = ttk.Frame(self)
        progress_frame.pack(fill="x", padx=10, pady=10)
        self.progress = ttk.Progressbar(progress_frame, maximum=100)
        self.progress.pack(fill="x")
        self.progress_info = ttk.Label(progress_frame, text="")
        self.progress_info.pack()

        # Download button
        self.download_btn = ttk.Button(self, text="Pobierz", command=self.start_download, state="disabled")
        self.download_btn.pack(pady=10)

        # Set initial states
        self.on_option_change()

    # -------------------------------------------------------------
    def fetch_info(self) -> None:
        """Validate URL and populate quality options."""
        url = normalize_url(self.url_var.get().strip())
        if not url:
            return
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'format': 'best'}) as ydl:
                self.yt = ydl.extract_info(url, download=False)
            self.info_label.config(text=f"Tytuł: {self.yt.get('title', 'Brak tytułu')}")
            self.populate_streams()
            self.download_btn.config(state="normal")
        except Exception as e:
            self.info_label.config(text=f"Nieprawidłowy link: {e}")
            self.download_btn.config(state="disabled")

    # -------------------------------------------------------------
    def populate_streams(self) -> None:
        """Fetch available quality streams."""
        formats = self.yt.get('formats', [])
        self.streams = {
            "video_sound": sorted([f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4'], key=lambda x: x.get('height', 0), reverse=True),
            "video_nosound": sorted([f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') == 'none' and f.get('ext') == 'mp4'], key=lambda x: x.get('height', 0), reverse=True),
            "audio": sorted([f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none'], key=lambda x: x.get('abr', 0), reverse=True),
        }
        self.populate_video_qualities()
        self.audio_box["values"] = [f"{s.get('abr', 0):.0f}kbps" for s in self.streams["audio"]]
        if self.audio_box["values"]:
            self.audio_box.current(0)
        self.update_filename()

    # -------------------------------------------------------------
    def populate_video_qualities(self) -> None:
        key = "video_sound" if self.video_sound_var.get() == "sound" else "video_nosound"
        self.video_box["values"] = list(dict.fromkeys([s['resolution'] for s in self.streams.get(key, [])])) # unique
        if self.video_box["values"]:
            self.video_box.current(0)
        self.update_filename()

    # -------------------------------------------------------------
    def sanitize(self, name: str) -> str:
        return re.sub(r'[\\/:*?"<>|]', '', name)

    # -------------------------------------------------------------
    def update_filename(self) -> None:
        if not self.yt:
            return
        title = self.sanitize(self.yt.get('title', 'video'))
        vq = self.video_quality.get()
        aq = self.audio_quality.get().replace('kbps', '')
        option = self.option_var.get()
        video_suffix = "film_w_sound" if self.video_sound_var.get() == "sound" else "film_no_sound"
        if option in ("video", "both"):
            self.video_filename.set(f"{title}-{vq}-{video_suffix}.mp4")
        else:
            self.video_filename.set("")
        if option in ("audio", "both"):
            self.audio_filename.set(f"{title}-{aq}kbps-music.mp3")
        else:
            self.audio_filename.set("")

    # -------------------------------------------------------------
    def on_option_change(self) -> None:
        """Enable/disable widgets depending on download option."""
        option = self.option_var.get()
        video_enabled = option in ("video", "both")
        audio_enabled = option in ("audio", "both")

        video_state = "normal" if video_enabled else "disabled"
        audio_state = "normal" if audio_enabled else "disabled"

        self.sound_rb.config(state=video_state)
        self.nosound_rb.config(state=video_state)
        self.video_box.config(state="readonly" if video_enabled else "disabled")
        self.video_entry.config(state="normal" if video_enabled else "disabled")
        if not video_enabled:
            self.video_quality.set("")
            self.video_filename.set("")
        else:
            if self.streams:
                self.populate_video_qualities()

        self.audio_box.config(state="readonly" if audio_enabled else "disabled")
        self.audio_entry.config(state="normal" if audio_enabled else "disabled")
        if not audio_enabled:
            self.audio_quality.set("")
            self.audio_filename.set("")

        self.update_filename()

    # -------------------------------------------------------------
    def choose_directory(self) -> None:
        directory = filedialog.askdirectory(initialdir=self.dir_var.get())
        if directory:
            self.dir_var.set(directory)

    # -------------------------------------------------------------
    def start_download(self) -> None:
        directory = self.dir_var.get()
        files_to_check = []
        option = self.option_var.get()
        if option in ("video", "both"):
            files_to_check.append(self.video_filename.get())
        if option in ("audio", "both"):
            files_to_check.append(self.audio_filename.get())
        for name in files_to_check:
            if os.path.exists(os.path.join(directory, name)):
                messagebox.showwarning("Istniejący plik", f"Plik {name} już istnieje.")
                return
        threading.Thread(target=self.download, daemon=True).start()

    # -------------------------------------------------------------
    def download(self) -> None:
        option = self.option_var.get()
        directory = self.dir_var.get()
        url = self.yt['webpage_url']

        def do_download(opts, filename):
            self.progress["value"] = 0
            opts['outtmpl'] = os.path.join(directory, filename)
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

        if option in ("video", "both"):
            stream = self.get_selected_video()
            if not stream: return
            opts = {'progress_hooks': [self.on_progress], 'format': stream['format_id']}
            do_download(opts, self.video_filename.get())

        if option in ("audio", "both"):
            stream = self.get_selected_audio()
            if not stream: return
            filename = self.audio_filename.get()
            base_filename, _ = os.path.splitext(filename)
            opts = {
                'progress_hooks': [self.on_progress],
                'format': stream['format_id'],
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
            }
            do_download(opts, base_filename)

        self.after(0, lambda: self.progress_info.config(text="Zakończono"))

    # -------------------------------------------------------------
    def get_selected_video(self):
        quality = self.video_quality.get()
        key = "video_sound" if self.video_sound_var.get() == "sound" else "video_nosound"
        for s in self.streams.get(key, []):
            if s['resolution'] == quality:
                return s
        return None

    # -------------------------------------------------------------
    def get_selected_audio(self):
        quality = self.audio_quality.get().replace('kbps', '')
        for s in self.streams.get("audio", []):
            if f"{s.get('abr', 0):.0f}" == quality:
                return s
        return None

    # -------------------------------------------------------------
    def on_progress(self, d) -> None:
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if not total:
                self.after(0, lambda: self.progress_info.config(text=f'Pobrano {downloaded/1024/1024:.2f} MB'))
                return
            percent = downloaded / total * 100
            speed = d.get('speed', 0) or 0
            remaining = d.get('eta', 0) or 0

            def _update():
                self.progress["value"] = percent
                info = (f"{percent:.1f}% | "
                        f"{downloaded/1024/1024:.2f}/{total/1024/1024:.2f} MB | "
                        f"{speed/1024:.2f} kB/s | "
                        f"{remaining:.1f} s do końca")
                self.progress_info.config(text=info)
            self.after(0, _update)
        elif d['status'] == 'finished':
            self.progress["value"] = 100
            self.after(0, lambda: self.progress_info.config(text="Pobieranie zakończone, przetwarzanie..."))


if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()
