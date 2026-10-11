import unittest
from types import SimpleNamespace
from util.movie_display import clean_title, select_movie, poster_variants, movie_caption

class MovieDisplayTests(unittest.TestCase):
    def test_clean_title_uses_filename_year(self):
        self.assertEqual(clean_title('Don Hindi 1080p', 'Don 2006 Hindi 1080p.mkv'), ('Don', 2006))

    def test_newest_exact_release_or_requested_year(self):
        releases = [
            {'media_type': 'movie', 'title': 'Don', 'release_date': '1978-05-12', 'poster_path': '/old'},
            {'media_type': 'movie', 'title': 'Don', 'release_date': '2006-10-20', 'poster_path': '/new'},
            {'media_type': 'movie', 'title': 'Donation', 'release_date': '2026-01-01', 'poster_path': '/wrong'},
        ]
        self.assertEqual(select_movie(releases, 'Don')['poster_path'], '/new')
        self.assertEqual(select_movie(releases, 'Don', 1978)['poster_path'], '/old')
        self.assertIsNone(select_movie(releases, 'Dune', 2021))

    def test_distinct_languages_only(self):
        posters = [{'iso_639_1': 'hi', 'file_path': '/hi'}, {'iso_639_1': 'en', 'file_path': '/en'}]
        self.assertEqual(poster_variants(posters, '/en'), ['/hi', '/en'])
        self.assertEqual(poster_variants(posters[:1], '/hi'), ['/hi'])

    def test_only_available_file_metadata(self):
        files = [SimpleNamespace(file_name='Don.2006.Hindi.1080p.mkv', caption='', file_size=2147483648)]
        caption = movie_caption({'title': 'Don', 'year': '2006', 'rating': 7.2, 'votes': 20}, files, 1)
        self.assertIn('Hindi', caption)
        self.assertIn('1080p', caption)
        self.assertIn('2.00 GB', caption)
        self.assertNotIn('English', caption)

if __name__ == '__main__':
    unittest.main()
