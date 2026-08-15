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

## Second review correction

The second visual review accepted the overall appearance and identified six
focused corrections before actual-size layout work:

- move month names slightly outward from the day-number band;
- remove the unexplained full declination circles from the equidistant view;
- show only the pole belonging to the rendered face;
- use the same neutral blue-grey for all three principal reference curves;
- enlarge principal-reference labels by 50 percent; and
- identify each diagnostic with the installed Wenu package version.

The correction keeps RA meridians and principal planes in the canonical
reference-sky path. Short declination marks are projected disk furniture, not
spherical parallels, so neither supported projection can turn them into full
circles. The preview uses the existing canonical footer and its
`importlib.metadata` version authority; no version string is hard coded.

The subsequent image review identified three long equidistant chords as
constellation segments whose endpoints both lay outside the face's
declination cap. Planar artist clipping retained the portion of each false
chord crossing the disk. Every point, curve, and grid is now clipped by
equatorial declination before either polar projection. Both ecliptic and
Galactic poles remain semantically requested; the same cap preparation
suppresses an out-of-face marker and its label.

The next south-face review found the automatic celestial-equator and ecliptic
labels occupying the same location. Automatic semantic reference labels now
share a render-local collision registry in normalized chart coordinates. Each
successful label reserves its position and later reference labels search their
own curve for the next separated interior candidate. Explicit anchors remain
authoritative.

Polar-planisphere reference labels retain their local tangent but use a
disk-specific orientation rule: typographic down points toward the celestial
pole at the disk center. Other chart families retain page-readable tangent
normalization.
