from pathlib import Path
import shutil

from astropy.utils.data import download_file


CATALOG_URL = (
    "https://cdsarc.cds.unistra.fr/ftp/I/239/ReadMe"
)

destination = Path(__file__).resolve().parent / "ReadMe"

cached_file = download_file(
    CATALOG_URL,
    cache=True,
    allow_insecure=True,
)

shutil.copyfile(cached_file, destination)

print(f"Catalog saved to: {destination}")
print(f"Size: {destination.stat().st_size:,} bytes")
