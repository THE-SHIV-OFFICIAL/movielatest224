import unittest
from types import SimpleNamespace as F
from util.file_filters import available, apply_filters


def f(name):
    return F(file_name=name, caption="", file_id=name)


FILES = [f("Mirzapur S01E01 720p Hindi WEB-DL.mkv"), f("Mirzapur S02E03 1080p Hindi English.mkv"),
         f("Mirzapur Season 3 480p Hindi.mkv"), f("Hera Pheri Part 2 2006 4K Hindi.mkv"),
         f("Shinchan The Movie 360p Tamil Dual Audio.mp4")]


class FilterTests(unittest.TestCase):
    def test_only_available_options(self):
        self.assertEqual([v for v, _ in available(FILES, "q")], ["360p", "480p", "720p", "1080p", "2160p"])
        self.assertEqual([v for v, _ in available(FILES, "s")], ["s1", "s2", "s3", "p2"])
        self.assertIn("dualaudio", [v for v, _ in available(FILES, "l")])
        self.assertNotIn("telugu", [v for v, _ in available(FILES, "l")])

    def test_combined_filters(self):
        self.assertEqual(len(apply_filters(FILES, {"s": "s2", "l": "english"})), 1)
        self.assertEqual(available(apply_filters(FILES, {"s": "s1"}), "q")[0][0], "720p")
        self.assertEqual(available([f("Movie 1080p.mkv")], "s"), [])


if __name__ == "__main__":
    unittest.main()
