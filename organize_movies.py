import argparse
import logging
import os
import re
import shutil
import sys
from pathlib import Path

import guessit
from imdb import Cinemagoer

DEFAULT_EXTENSIONS = (".mp4", ".mkv", ".avi", ".srt", ".sub", ".wmv", ".mov")


def sanitize_filename(name):
    """Remove invalid characters for Windows paths to ensure clean folder names."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "", str(name))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or "Unknown"


def normalize_extensions(raw_extensions):
    normalized = []
    for ext in raw_extensions or []:
        candidate = ext.strip().lower()
        if not candidate:
            continue
        if not candidate.startswith("."):
            candidate = f".{candidate}"
        normalized.append(candidate)
    return tuple(dict.fromkeys(normalized)) or DEFAULT_EXTENSIONS


def resolve_destination(directory: Path, filename: str) -> Path:
    target_path = directory / filename
    if not target_path.exists():
        return target_path

    stem, suffix = os.path.splitext(filename)
    counter = 1
    while True:
        candidate = directory / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def build_parser():
    parser = argparse.ArgumentParser(
        description="Organize movie files into folders named by title and year."
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path(os.environ.get("MOVIE_DIR", r"C:\Movies")),
        help="Directory containing the movie files to organize (default: C:\\Movies or MOVIE_DIR).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the move without moving any files.",
    )
    parser.add_argument(
        "--extensions",
        nargs="*",
        default=list(DEFAULT_EXTENSIONS),
        help="Extensions to process, such as .mp4 .mkv .srt.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show more detailed runtime logging.",
    )
    return parser


def get_folder_name(title, year, ia, cache):
    if not title:
        return None

    year_text = str(year) if year else None
    cache_key = (str(title).lower(), year_text)
    if cache_key in cache:
        return cache[cache_key]

    logging.info("Querying IMDb for '%s' (Year: %s)...", title, year_text)
    try:
        search_results = ia.search_movie(title)
        if not search_results:
            safe_title = sanitize_filename(title).title()
            folder_name = f"{year_text} {safe_title}" if year_text else safe_title
        else:
            best_match = search_results[0]
            if year_text:
                for result in search_results:
                    result_year = str(result.get("year", ""))
                    if result_year == year_text:
                        best_match = result
                        break

            official_title = best_match.get("title") or title
            official_year = best_match.get("year")
            safe_title = sanitize_filename(official_title)
            folder_name = f"{official_year} {safe_title}" if official_year else safe_title

        cache[cache_key] = folder_name
        logging.info("Decided on folder: %s", folder_name)
        return folder_name
    except Exception as exc:  # pragma: no cover - network failure path
        logging.warning("Error accessing IMDb for '%s': %s", title, exc)
        safe_title = sanitize_filename(title).title()
        fallback_name = f"{year_text} {safe_title}" if year_text else safe_title
        cache[cache_key] = fallback_name
        return fallback_name


def main():
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    source_dir = args.source_dir.resolve()
    supported_extensions = normalize_extensions(args.extensions)

    if not source_dir.exists():
        logging.error("Source directory does not exist: %s", source_dir)
        return 1
    if not source_dir.is_dir():
        logging.error("Source path is not a directory: %s", source_dir)
        return 1

    ia = Cinemagoer()
    imdb_cache = {}
    processed = 0
    moved = 0

    for media_path in sorted(source_dir.iterdir()):
        if media_path.is_dir():
            continue

        ext = media_path.suffix.lower()
        if ext not in supported_extensions:
            continue

        logging.info("Processing: %s", media_path.name)
        filename = media_path.name
        guess = guessit.guessit(filename)
        title = guess.get("title")
        year = guess.get("year")

        if not title:
            logging.warning("Skipped '%s': could not deduce a movie title.", filename)
            continue

        processed += 1
        folder_name = get_folder_name(title, year, ia, imdb_cache)
        if not folder_name:
            logging.warning("Skipped '%s': no usable folder name could be derived.", filename)
            continue

        folder_path = source_dir / folder_name
        folder_path.mkdir(exist_ok=True, parents=True)
        destination = resolve_destination(folder_path, filename)

        if args.dry_run:
            logging.info("Would move %s -> %s", media_path, destination)
            continue

        try:
            shutil.move(str(media_path), str(destination))
            logging.info("Moved %s -> %s", media_path.name, destination.relative_to(source_dir))
            moved += 1
        except OSError as exc:
            logging.error("Failed moving %s: %s", filename, exc)

    logging.info("Processed %s file(s); moved %s file(s).", processed, moved)
    return 0


if __name__ == "__main__":
    sys.exit(main())
