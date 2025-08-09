import os
import re
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pytube import YouTube


class YouTubeDownloader(tk.Tk):
    """Simple cross-platform YouTube downloader with GUI."""

    def __init__(self) -> None:
        super().__init__()
        self.title("YT Downloader")
        self.geometry("700x500")
        self.resizable(False, False)
        self.yt = None
        self.streams = {}
        self.start_time = None

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
        url_entry.bind("<Return>", lambda e: self.fetch_info())
        url_entry.bind("<FocusOut>", lambda e: self.fetch_info())
        self.info_label = ttk.Label(self, text="Wprowadź link do filmu.")
        self.info_label.pack(pady=5)

        # Download type options
        option_frame = ttk.LabelFrame(self, text="Rodzaj pobierania")
        option_frame.pack(fill="x", padx=10, pady=5)
        self.option_var = tk.StringVar(value="video")
        ttk.Radiobutton(option_frame, text="Film", variable=self.option_var,
                        value="video", command=self.update_filename).pack(side="left", padx=5)
        ttk.Radiobutton(option_frame, text="Muzyka", variable=self.option_var,
                        value="audio", command=self.update_filename).pack(side="left", padx=5)
        ttk.Radiobutton(option_frame, text="Film + Muzyka", variable=self.option_var,
                        value="both", command=self.update_filename).pack(side="left", padx=5)

        # Video sound options
        video_type_frame = ttk.Frame(self)
        video_type_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(video_type_frame, text="Wideo:").pack(side="left")
        self.video_sound_var = tk.StringVar(value="sound")
        ttk.Radiobutton(video_type_frame, text="z dźwiękiem", variable=self.video_sound_var,
                        value="sound", command=self.populate_video_qualities).pack(side="left", padx=5)
        ttk.Radiobutton(video_type_frame, text="bez dźwięku", variable=self.video_sound_var,
                        value="nosound", command=self.populate_video_qualities).pack(side="left", padx=5)

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

    # -------------------------------------------------------------
    def fetch_info(self) -> None:
        """Validate URL and populate quality options."""
        url = self.url_var.get().strip()
        if not url:
            return
        try:
            self.yt = YouTube(url, on_progress_callback=self.on_progress)
            self.info_label.config(text=f"Tytuł: {self.yt.title}")
            self.populate_streams()
            self.download_btn.config(state="normal")
        except Exception:
            self.info_label.config(text="Nieprawidłowy link")
            self.download_btn.config(state="disabled")

    # -------------------------------------------------------------
    def populate_streams(self) -> None:
        """Fetch available quality streams."""
        self.streams = {
            "video_sound": self.yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc(),
            "video_nosound": self.yt.streams.filter(only_video=True, file_extension="mp4").order_by("resolution").desc(),
            "audio": self.yt.streams.filter(only_audio=True).order_by("abr").desc(),
        }
        self.populate_video_qualities()
        self.audio_box["values"] = [s.abr for s in self.streams["audio"]]
        if self.audio_box["values"]:
            self.audio_box.current(0)
        self.update_filename()

    # -------------------------------------------------------------
    def populate_video_qualities(self) -> None:
        key = "video_sound" if self.video_sound_var.get() == "sound" else "video_nosound"
        self.video_box["values"] = [s.resolution for s in self.streams.get(key, [])]
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
        title = self.sanitize(self.yt.title)
        vq = self.video_quality.get()
        aq = self.audio_quality.get()
        option = self.option_var.get()
        video_suffix = "film_w_sound" if self.video_sound_var.get() == "sound" else "film_no_sound"
        if option in ("video", "both"):
            self.video_filename.set(f"{title}-{vq}-{video_suffix}.mp4")
            self.video_entry.config(state="normal")
        else:
            self.video_filename.set("")
            self.video_entry.config(state="disabled")
        if option in ("audio", "both"):
            self.audio_filename.set(f"{title}-{aq}-music.mp3")
            self.audio_entry.config(state="normal")
        else:
            self.audio_filename.set("")
            self.audio_entry.config(state="disabled")

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
        if option in ("video", "both"):
            stream = self.get_selected_video()
            self.progress["value"] = 0
            self.start_time = time.time()
            stream.download(output_path=directory, filename=self.video_filename.get())
        if option in ("audio", "both"):
            stream = self.get_selected_audio()
            self.progress["value"] = 0
            self.start_time = time.time()
            stream.download(output_path=directory, filename=self.audio_filename.get())
        self.after(0, lambda: self.progress_info.config(text="Zakończono"))

    # -------------------------------------------------------------
    def get_selected_video(self):
        quality = self.video_quality.get()
        key = "video_sound" if self.video_sound_var.get() == "sound" else "video_nosound"
        for s in self.streams.get(key, []):
            if s.resolution == quality:
                return s
        return None

    # -------------------------------------------------------------
    def get_selected_audio(self):
        quality = self.audio_quality.get()
        for s in self.streams.get("audio", []):
            if s.abr == quality:
                return s
        return None

    # -------------------------------------------------------------
    def on_progress(self, stream, chunk, bytes_remaining) -> None:
        total = stream.filesize
        downloaded = total - bytes_remaining
        percent = downloaded / total * 100
        elapsed = time.time() - self.start_time if self.start_time else 0
        speed = downloaded / elapsed if elapsed > 0 else 0
        remaining = bytes_remaining / speed if speed > 0 else 0

        def _update():
            self.progress["value"] = percent
            info = (f"{percent:.1f}% | "
                    f"{downloaded/1024/1024:.2f}/{total/1024/1024:.2f} MB | "
                    f"{speed/1024:.2f} kB/s | "
                    f"{remaining:.1f} s do końca")
            self.progress_info.config(text=info)

        self.after(0, _update)


if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()
