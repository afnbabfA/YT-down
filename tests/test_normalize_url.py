import youtube_downloader as yd


def test_short_url_si_param_removed():
    url = "https://youtu.be/nw8kLJoMUMw?si=GiAjA4L1LoFjsqpl"
    assert yd.normalize_url(url) == "https://youtu.be/nw8kLJoMUMw"


def test_watch_url_si_param_removed():
    url = "https://www.youtube.com/watch?v=nw8kLJoMUMw&si=abc"
    assert yd.normalize_url(url) == "https://www.youtube.com/watch?v=nw8kLJoMUMw"


def test_watch_url_preserves_other_params():
    url = "https://www.youtube.com/watch?v=nw8kLJoMUMw&t=30s&si=abc"
    expected = "https://www.youtube.com/watch?v=nw8kLJoMUMw&t=30s"
    assert yd.normalize_url(url) == expected
