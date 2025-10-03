import unittest
from youtube_downloader import YouTubeDownloader

class TestYtDlpIntegration(unittest.TestCase):
    def test_fetch_info_with_yt_dlp(self):
        app = YouTubeDownloader()
        # A well-known video URL
        app.url_var.set("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        app.fetch_info()

        button_state = app.download_btn.cget("state")
        print(f"Button state: {button_state}")
        print(f"Button state type: {type(button_state)}")

        self.assertIn("Rick Astley", app.info_label.cget("text"))
        self.assertTrue(len(app.streams["video_sound"]) > 0)
        self.assertTrue(len(app.streams["video_nosound"]) > 0)
        self.assertTrue(len(app.streams["audio"]) > 0)
        self.assertEqual(str(button_state), "normal")

if __name__ == '__main__':
    unittest.main()