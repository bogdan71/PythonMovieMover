import os
import shutil
import re
import guessit
from imdb import Cinemagoer

def sanitize_filename(name):
    """Remove invalid characters for Windows paths to ensure clean folder names."""
    return re.sub(r'[\\/*?:"<>|]', "", str(name)).strip()

def main():
    target_dir = r"C:\Users\bogus\Downloads\Movies"
    ia = Cinemagoer()
    
    # Cache to avoid repetitive API calls for files of the same movie
    imdb_cache = {}

    for filename in os.listdir(target_dir):
        file_path = os.path.join(target_dir, filename)
        
        # Skip evaluating directories
        if os.path.isdir(file_path):
            continue
            
        # Work only with media and subtitle files
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.mp4', '.mkv', '.avi', '.srt', '.sub', '.wmv', '.mov']:
            continue

        print(f"Processing: {filename}")
        
        # Guess movie metadata from filename
        guess = guessit.guessit(filename)
        title = guess.get('title')
        year = guess.get('year')
        
        if not title:
            print(f"  Skipped (Could not deduce title).")
            continue
            
        # Treat year string just in case
        year = str(year) if year else None
        cache_key = (str(title).lower(), year)
        
        if cache_key in imdb_cache:
            folder_name = imdb_cache[cache_key]
        else:
            print(f"  Querying IMDb for '{title}' (Year: {year})...")
            try:
                search_results = ia.search_movie(title)
                
                if not search_results:
                    print(f"  No result found on IMDb. Proceeding with filename guess.")
                    safe_title = sanitize_filename(title).title()
                    folder_name = f"{year} {safe_title}" if year else safe_title
                else:
                    best_match = search_results[0] # Default to top choice
                    # Find an exact year match if we parsed one
                    if year:
                        for result in search_results:
                            result_year = str(result.get('year', ''))
                            if result_year == year:
                                best_match = result
                                break
                    
                    official_title = best_match.get('title')
                    official_year = best_match.get('year')
                    
                    safe_title = sanitize_filename(official_title)
                    if official_year:
                        folder_name = f"{official_year} {safe_title}"
                    else:
                        folder_name = safe_title
                
                imdb_cache[cache_key] = folder_name
                print(f"  Decided on folder: {folder_name}")
                
            except Exception as e:
                print(f"  Error accessing IMDb: {e}")
                continue

        # Make the actual directory
        target_folder_path = os.path.join(target_dir, folder_name)
        if not os.path.exists(target_folder_path):
            os.makedirs(target_folder_path)
            
        # Ship it
        target_file_path = os.path.join(target_folder_path, filename)
        try:
            shutil.move(file_path, target_file_path)
            print(f"  Moved -> {folder_name}\\{filename}")
        except Exception as e:
            print(f"  Failed moving {filename}: {e}")
            
if __name__ == "__main__":
    main()
