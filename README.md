# YT-down

Prosta aplikacja z graficznym interfejsem do pobierania filmów i muzyki z YouTube.

## Wymagania

- Python 3.10+
- Zależności z pliku `requirements.txt` (instalacja: `pip install -r requirements.txt`)

## Uruchomienie z kodu źródłowego

```bash
python youtube_downloader.py
```

## Budowanie aplikacji

Do stworzenia samodzielnych aplikacji użyj [PyInstaller](https://pyinstaller.org/):

### Windows

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile youtube_downloader.py
```
Powstały plik `dist/youtube_downloader.exe` można skopiować w dowolne miejsce.

### macOS

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile youtube_downloader.py
```
Plik `dist/youtube_downloader` może być uruchomiony na macOS.

Domyślny katalog pobierania to folder `Pobrane` w katalogu domowym użytkownika.
