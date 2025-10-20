# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import pathlib

from anki.collection import Collection

from media_converter.media_deduplication.deduplication import MediaDedup

COL_PATH = pathlib.Path.home() / ".local/share/Anki2/shared decks [Ankiweb]/collection.anki2"


def main() -> None:
    col = Collection(str(COL_PATH.absolute()))
    try:
        dedup = MediaDedup(col=col)
        print("collecting files...")
        files = dedup.collect_files()
        for dup, orig in files.items():
            print(f"{dup.name} => {orig.name}")
        print("replacing links...")
        dedup.deduplicate(files)
        print("done.")
    finally:
        col.close()


if __name__ == "__main__":
    main()
