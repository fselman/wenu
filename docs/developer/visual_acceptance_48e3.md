# Milestone 48E.3 polar reference review

Fernando accepted the overall white-and-blue Milestone 48E.2 appearance after
the first genuine north/south preview. He requested a second rendering with
tighter calendar hierarchy, contained constellation labels, +20/-20-degree
overlap, corrected stereographic handedness, and the essential grid and
reference overlays.

After applying Milestone 48E.3 and passing tests, regenerate the canonical pair:

```bash
python tools/render_48e2_polar_preview.py
```

Review `polar-planisphere-south.png` and `polar-planisphere-north.png` together:

- labelled-day ticks are darker but equal in length to ordinary daily ticks;
- day numbers sit close to their marks;
- month names share the day-number band at twice the font size;
- no constellation label enters the date ring;
- the two faces overlap from declination -20 through +20 degrees;
- RA meridians lie at 0h, 6h, 12h, and 18h;
- those meridians carry short declination ticks every 20 degrees;
- the celestial equator, ecliptic, and Galactic plane are labelled;
- ecliptic cardinal points and the relevant ecliptic and Galactic poles are
  present but remain subordinate to the stars.

Regenerate the comparison separately:

```bash
python tools/render_48e2_polar_preview.py \
  --projection stereographic \
  --output output/48e3-polar-preview-stereographic
```

Verify stereographic east-west direction against the accepted equidistant
face, not merely the fact that the two printed faces fold back to back.
Actual-size page layout, translation, and final typography remain later work.
