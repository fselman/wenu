"""Compatibility review adapter for the installed atlas index owner."""

import argparse
from pathlib import Path

from wenu.charts.atlas_index import plot_overview

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("design", type=Path, help="Resolved band-tiling JSON")
    parser.add_argument("output_prefix", type=Path, help="New versioned filename without extension")
    parser.add_argument("--footprints", action="store_true", help="Overlay sampled complete rectangular footprints")
    parser.add_argument("--joined", action="store_true", help="Compose overlapping disk contours at the inward equatorial point")
    parser.add_argument("--astronomy", action="store_true", help="Add native ICRS catalogue stars, constellations and Milky Way")
    parser.add_argument("--star-magnitude-limit", type=float, default=5.5)
    parser.add_argument("--include-lowest-mw-isophote", action="store_true",
                        help="Add the faint OL1 envelope to OL2–OL5; requires --astronomy")
    parser.add_argument("--magellanic-clouds", action="store_true",
                        help="Add all four LMC and SMC isophotes; requires --astronomy")
    args = parser.parse_args()
    for path in plot_overview(args.design, args.output_prefix, footprints=args.footprints,
                              joined=args.joined, astronomy=args.astronomy,
                              star_magnitude_limit=args.star_magnitude_limit,
                              include_lowest_mw_isophote=args.include_lowest_mw_isophote,
                              magellanic_clouds=args.magellanic_clouds):
        print(path)


if __name__ == "__main__":
    main()
