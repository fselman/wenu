#!/usr/bin/env bash

set -euo pipefail

wenu_chart regional \
  --config "$HOME/Documents/wenu-virgo-opaque-mask.toml" \
  --observer-location "La Ligua" \
  --observer-time "2026-09-06T22:00:00-04:00" \
  --center-altitude 20deg \
  --center-azimuth 270deg \
  --field-width 60 \
  --field-height 50 \
  --orientation zenith-up \
  --style cartoon \
  --mode presentation \
  --language es \
  --constellation-lines Vir \
  --constellation-labels Vir \
  --constellation-mask Vir \
  --horizon \
  --horizon-mask \
  --magnitude-limit 5.0 \
  --title "Virgo poniéndose — 6 sep 22:00" \
  --output output/virgo-setting-2026_09_06T2200.png
