import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import organize_movies


class DryRunTests(unittest.TestCase):
    def test_dry_run_does_not_create_destination_folder_or_move_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            movie_path = source_dir / "Example.Movie.2020.mkv"
            movie_path.write_text("movie content", encoding="utf-8")
            destination_dir = source_dir / "2020 Example Movie"

            with (
                patch(
                    "sys.argv",
                    [
                        "organize_movies.py",
                        "--source-dir",
                        str(source_dir),
                        "--dry-run",
                        "--verbose",
                    ],
                ),
                patch(
                    "organize_movies.guessit.guessit",
                    return_value={"title": "Example Movie", "year": 2020},
                ),
                patch("organize_movies.Cinemagoer") as cinemagoer_class,
            ):
                cinemagoer_class.return_value.search_movie.return_value = [
                    {"title": "Example Movie", "year": 2020}
                ]
                result = organize_movies.main()

            self.assertEqual(result, 0)
            self.assertTrue(movie_path.is_file())
            self.assertEqual(movie_path.read_text(encoding="utf-8"), "movie content")
            self.assertFalse(destination_dir.exists())


if __name__ == "__main__":
    unittest.main()
