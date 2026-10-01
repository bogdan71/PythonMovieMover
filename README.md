# PythonMovieMover

A small utility that scans a directory of movie files, guesses each title from the filename, looks up metadata on IMDb, and moves each item into a folder named after the discovered title and year.

## Setup

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Usage

```bash
python organize_movies.py --source-dir "C:\Movies"
python organize_movies.py --source-dir "C:\Movies" --dry-run --verbose
```

You can also point at a different folder with `MOVIE_DIR`:

```bash
$env:MOVIE_DIR = "D:\Downloads\Movies"
python organize_movies.py
```

## Notes

- The script skips folders and only processes configured file extensions.
- `--dry-run` previews moves without changing the filesystem.
- If IMDb cannot resolve a title, the script falls back to the filename-derived title instead of stopping.
