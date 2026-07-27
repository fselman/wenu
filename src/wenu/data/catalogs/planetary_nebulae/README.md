# Strasbourg–ESO Galactic planetary-nebula catalogue

This directory contains Wenu's normalized snapshot of the 1,143 true
or probable planetary nebulae in the HEASARC `plnebulae` table. That
table derives from the 1992 Strasbourg–ESO catalogue (CDS V/84).

This is a stable historical source, not a current census. HASH is the
modern primary compilation of Galactic planetary nebulae.

Regenerate the snapshot from the repository root with:

```shell
python tools/query_planetary_nebulae_heasarc.py
```

Please cite Acker et al. (1992) and HEASARC when using these data.
