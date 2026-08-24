#!/usr/bin/env bash

set -euo pipefail

wenu_chart planisphere \
  --config "$HOME/Documents/wenu-la-ligua-sin-dso.toml" \
  --observer-location "La Ligua" \
  --observer-time "2026-08-21T21:00:00-04:00" \
  --style atlas \
  --mode presentation \
  --language es \
  --magnitude-limit 5.0 \
  --equatorial-grid \
  --equatorial-grid-labels \
  --grid-references equatorial \
  --title "Cielo de La Ligua — 21 de agosto de 2026, 21:00" \
  --output output/la-ligua-2026-08-21-2100-stereographic.png
