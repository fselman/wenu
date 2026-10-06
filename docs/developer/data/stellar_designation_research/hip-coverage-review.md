# HIP designation coverage review

Candidate based on PR #207 at `8aec3417`. Source Wikidata claims and the
original 77-case dossier remain unchanged. These are authored cross-index
findings, not new Wikidata statements or physical-component identifications.
The runtime table is [curation.json](../../../../src/wenu/data/catalogs/star_designations/curation.json).

There are 158 curated missing-kind associations (64 Bayer, 94 Flamsteed),
68 pending coverage candidates and 58 existing-kind variant discrepancies.
The `Selman` column is reserved for Fernando's decisions and remains blank.

## Coverage gaps

| HIP | V (Hipparcos) | Kind | Effective added code | Status | Source values | Selman |
| ---: | ---: | --- | --- | --- | --- | --- |
| 2484 | 4.36 | bayer | β¹ Tuc | cross_index_curated | BSC: β¹ Tuc; HYG: β¹ Tuc; Kostjuk: β¹ Tuc | |
| 2487 | 4.53 | bayer | β² Tuc | cross_index_curated | BSC: β² Tuc; HYG: β² Tuc; Kostjuk: β² Tuc | |
| 2548 | 5.69 | flamsteed | 51 Psc | cross_index_curated | BSC: 51 Psc; HYG: 51 Psc; Kostjuk: 51 Psc | |
| 2578 | 5.07 | bayer | β³ Tuc | cross_index_curated | BSC: β³ Tuc; HYG: β³ Tuc; Kostjuk: β³ Tuc | |
| 3478 | 5.66 | flamsteed |  | pending | Kostjuk: 68 Cas | |
| 4084 | 6.67 | bayer | λ¹ Tuc | cross_index_curated | BSC: λ¹ Tuc; HYG: λ¹ Tuc; Kostjuk: λ¹ Tuc | |
| 4843 | 6.9 | bayer |  | pending | Kostjuk: υ Cep | |
| 5131 | 5.33 | bayer | ψ¹ Psc | cross_index_curated | BSC: ψ¹ Psc; HYG: ψ¹ Psc; Kostjuk: ψ¹ Psc | |
| 5131 | 5.33 | flamsteed | 74 Psc | cross_index_curated | BSC: 74 Psc; HYG: 74 Psc; Kostjuk: 74 Psc | |
| 5132 | 5.55 | bayer | ψ¹ Psc | cross_index_curated | BSC: ψ¹ Psc; HYG: ψ¹ Psc; Kostjuk: ψ¹ Psc | |
| 5132 | 5.55 | flamsteed | 74 Psc | cross_index_curated | BSC: 74 Psc; HYG: 74 Psc; Kostjuk: 74 Psc | |
| 5144 | 7.26 | flamsteed | 77 Psc | cross_index_curated | BSC: 77 Psc; HYG: 77 Psc; Kostjuk: 77 Psc | |
| 5737 | 5.21 | bayer | ζ Psc | cross_index_curated | BSC: ζ Psc; HYG: ζ Psc; Kostjuk: ζ Psc; WGSN: ζ Psc | |
| 5737 | 5.21 | flamsteed | 86 Psc | cross_index_curated | BSC: 86 Psc; HYG: 86 Psc; Kostjuk: 86 Psc | |
| 5743 | 6.44 | bayer | ζ Psc | cross_index_curated | BSC: ζ Psc; HYG: ζ Psc; Kostjuk: ζ Psc; WGSN: ζ Psc | |
| 5743 | 6.44 | flamsteed | 86 Psc | cross_index_curated | BSC: 86 Psc; HYG: 86 Psc; Kostjuk: 86 Psc | |
| 5799 | 5.14 | flamsteed | 37 Cet | cross_index_curated | BSC: 37 Cet; HYG: 37 Cet; Kostjuk: 37 Cet | |
| 5896 | 4.25 | bayer | κ Tuc | cross_index_curated | BSC: κ Tuc; HYG: κ Tuc; Kostjuk: κ Tuc | |
| 8240 | 5.49 | flamsteed |  | pending | Kostjuk: 120 Phe | |
| 9155 | 8.89 | flamsteed |  | pending | Kostjuk: 58 Cet | |
| 9383 | 8.86 | bayer |  | pending | Kostjuk: χ Tri | |
| 9631 | 5.96 | flamsteed | 61 Cet | cross_index_curated | BSC: 61 Cet; HYG: 61 Cet; Kostjuk: 61 Cet | |
| 10176 | 6.09 | flamsteed | 59 And | cross_index_curated | BSC: 59 And; HYG: 59 And; Kostjuk: 59 And | |
| 10180 | 6.82 | flamsteed | 59 And | cross_index_curated | BSC: 59 And; HYG: 59 And; Kostjuk: 59 And | |
| 10305 | 5.65 | flamsteed | 66 Cet | cross_index_curated | BSC: 66 Cet; HYG: 66 Cet; Kostjuk: 66 Cet | |
| 12184 | 7.1 | flamsteed | 30 Ari | cross_index_curated | BSC: 30 Ari; HYG: 30 Ari; Kostjuk: 30 Ari | |
| 12189 | 6.48 | flamsteed | 30 Ari | cross_index_curated | BSC: 30 Ari; HYG: 30 Ari; Kostjuk: 30 Ari | |
| 13531 | 3.93 | flamsteed | 18 Per | cross_index_curated | BSC: 18 Per; HYG: 18 Per; Kostjuk: 18 Per | |
| 13879 | 4.68 | flamsteed | 22 Per | cross_index_curated | BSC: 22 Per; HYG: 22 Per; Kostjuk: 22 Per | |
| 13942 | 5.69 | bayer | ζ For | cross_index_curated | BSC: ζ For; HYG: ζ For; Kostjuk: ζ For | |
| 14668 | 3.79 | flamsteed | 27 Per | cross_index_curated | BSC: 27 Per; HYG: 27 Per; Kostjuk: 27 Per | |
| 14817 | 4.61 | flamsteed | 28 Per | cross_index_curated | BSC: 28 Per; HYG: 28 Per; Kostjuk: 28 Per | |
| 14915 | 5.55 | bayer |  | pending | Kostjuk: g Tau | |
| 15330 | 5.53 | bayer | ζ¹ Ret | cross_index_curated | BSC: ζ¹ Ret; HYG: ζ¹ Ret; Kostjuk: ζ¹ Ret | |
| 15371 | 5.24 | bayer | ζ² Ret | cross_index_curated | BSC: ζ² Ret; HYG: ζ² Ret; Kostjuk: ζ² Ret | |
| 15510 | 4.26 | flamsteed |  | pending | Kostjuk: 82 Eri | |
| 16245 | 4.71 | bayer | κ Ret | cross_index_curated | BSC: κ Ret; HYG: κ Ret; Kostjuk: κ Ret | |
| 16335 | 4.36 | flamsteed | 35 Per | cross_index_curated | BSC: 35 Per; HYG: 35 Per; Kostjuk: 35 Per | |
| 16826 | 4.32 | flamsteed | 37 Per | cross_index_curated | BSC: 37 Per; HYG: 37 Per; Kostjuk: 37 Per | |
| 17358 | 3.01 | flamsteed | 39 Per | cross_index_curated | BSC: 39 Per; HYG: 39 Per; Kostjuk: 39 Per | |
| 17529 | 3.77 | flamsteed | 41 Per | cross_index_curated | BSC: 41 Per; HYG: 41 Per; Kostjuk: 41 Per | |
| 18141 | 5.48 | flamsteed | 30 Eri | cross_index_curated | BSC: 30 Eri; HYG: 30 Eri; Kostjuk: 30 Eri | |
| 19335 | 5.52 | flamsteed | 50 Per | cross_index_curated | BSC: 50 Per; HYG: 50 Per; Kostjuk: 50 Per | |
| 19780 | 3.33 | bayer | α Ret | cross_index_curated | BSC: α Ret; HYG: α Ret; Kostjuk: α Ret; WGSN: α Ret | |
| 19812 | 4.12 | flamsteed | 51 Per | cross_index_curated | BSC: 51 Per; HYG: 51 Per; Kostjuk: 51 Per | |
| 19849 | 4.43 | bayer | ο² Eri | cross_index_curated | BSC: ο² Eri; HYG: ο² Eri; Kostjuk: ο² Eri; WGSN: ο² Eri | |
| 19849 | 4.43 | flamsteed | 40 Eri | cross_index_curated | BSC: 40 Eri; HYG: 40 Eri; Kostjuk: 40 Eri | |
| 19921 | 4.44 | bayer | ε Ret | cross_index_curated | BSC: ε Ret; HYG: ε Ret; Kostjuk: ε Ret | |
| 20234 | 5.55 | bayer |  | pending | Kostjuk: b² Per | |
| 22531 | 5.58 | bayer | ι Pic | cross_index_curated | BSC: ι Pic; HYG: ι Pic; Kostjuk: ι Pic | |
| 22534 | 6.42 | bayer | ι Pic | cross_index_curated | BSC: ι Pic; HYG: ι Pic; Kostjuk: ι Pic | |
| 22994 | 6.65 | flamsteed |  | pending | HYG: 6 Cam | |
| 24727 | 4.54 | flamsteed | 16 Aur | cross_index_curated | BSC: 16 Aur; HYG: 16 Aur; Kostjuk: 16 Aur | |
| 25145 | 7.17 | bayer |  | pending | Kostjuk: m Ori | |
| 25145 | 7.17 | flamsteed |  | pending | Kostjuk: 23 Ori | |
| 25303 | 6.26 | bayer | θ Pic | cross_index_curated | BSC: θ Pic; HYG: θ Pic; Kostjuk: θ Pic | |
| 25695 | 5.47 | flamsteed | 118 Tau | cross_index_curated | BSC: 118 Tau; HYG: 118 Tau; Kostjuk: 118 Tau | |
| 25776 | 6.18 | flamsteed |  | pending | Kostjuk: 31 Men | |
| 26001 | 5.34 | flamsteed |  | pending | Kostjuk: 28 Dor | |
| 26220 | 4.98 | flamsteed | 41 Ori | cross_index_curated | BSC: 41 Ori; HYG: 41 Ori; Kostjuk: 41 Ori | |
| 26221 | 5.13 | flamsteed | 41 Ori | cross_index_curated | BSC: 41 Ori; HYG: 41 Ori; Kostjuk: 41 Ori | |
| 26224 | 6.71 | flamsteed | 41 Ori | cross_index_curated | BSC: 41 Ori; HYG: 41 Ori; Kostjuk: 41 Ori | |
| 27890 | 4.65 | flamsteed |  | pending | Kostjuk: 36 Dor | |
| 28561 | 6.36 | flamsteed |  | pending | Kostjuk: 141 Tau | |
| 28756 | 5.65 | flamsteed |  | pending | Kostjuk: 72 Col | |
| 30419 | 4.39 | bayer | ε Mon | cross_index_curated | BSC: ε Mon; HYG: ε Mon; Kostjuk: ε Mon | |
| 30419 | 4.39 | flamsteed | 8 Mon | cross_index_curated | BSC: 8 Mon; HYG: 8 Mon; Kostjuk: 8 Mon | |
| 30422 | 6.72 | bayer |  | pending | Kostjuk: ε Mon | |
| 30422 | 6.72 | flamsteed |  | pending | Kostjuk: 8 Mon | |
| 30756 | 8.59 | flamsteed |  | pending | Kostjuk: 15 Gem | |
| 30932 | 5.2 | flamsteed |  | pending | Kostjuk: 61 Pic | |
| 31158 | 6.26 | flamsteed |  | pending | HYG: 20 Gem; Kostjuk: 20 Gem | |
| 31978 | 4.66 | flamsteed | 15 Mon | cross_index_curated | BSC: 15 Mon; HYG: 15 Mon; Kostjuk: 15 Mon | |
| 33779 | 5.14 | flamsteed |  | pending | Kostjuk: 23 Car | |
| 34473 | 5.68 | bayer | γ¹ Vol | cross_index_curated | BSC: γ¹ Vol; HYG: γ¹ Vol; Kostjuk: γ¹ Vol | |
| 34481 | 3.78 | bayer | γ² Vol | cross_index_curated | BSC: γ² Vol; HYG: γ² Vol; Kostjuk: γ² Vol | |
| 35210 | 4.83 | flamsteed |  | pending | Kostjuk: 145 CMa | |
| 35726 | 7.72 | flamsteed |  | pending | Kostjuk: 20 Lyn | |
| 35731 | 7.49 | flamsteed |  | pending | HYG: 20 Lyn | |
| 35783 | 6.86 | flamsteed | 19 Lyn | cross_index_curated | BSC: 19 Lyn; HYG: 19 Lyn; Kostjuk: 19 Lyn | |
| 35785 | 5.8 | flamsteed | 19 Lyn | cross_index_curated | BSC: 19 Lyn; HYG: 19 Lyn; Kostjuk: 19 Lyn | |
| 36817 | 5.06 | bayer |  | pending | Kostjuk: n Pup | |
| 37322 | 5.73 | bayer |  | pending | Kostjuk: d² Pup | |
| 37379 | 4.98 | flamsteed |  | pending | Kostjuk: 140 Pup | |
| 37504 | 3.93 | bayer | ζ Vol | cross_index_curated | BSC: ζ Vol; HYG: ζ Vol; Kostjuk: ζ Vol | |
| 37842 | 7.03 | flamsteed | 2 Pup | cross_index_curated | BSC: 2 Pup; HYG: 2 Pup; Kostjuk: 2 Pup | |
| 37843 | 6.06 | flamsteed | 2 Pup | cross_index_curated | BSC: 2 Pup; HYG: 2 Pup; Kostjuk: 2 Pup | |
| 37853 | 5.36 | flamsteed |  | pending | Kostjuk: 171 Pup | |
| 38146 | 5.32 | flamsteed |  | pending | Kostjuk: 188 Pup | |
| 38423 | 5.01 | flamsteed |  | pending | Kostjuk: 212 Pup | |
| 39311 | 4.39 | bayer |  | pending | Kostjuk: G CMi | |
| 40282 | 5.52 | flamsteed |  | pending | Kostjuk: 16 Vel | |
| 40817 | 5.33 | bayer | κ¹ Vol | cross_index_curated | BSC: κ¹ Vol; HYG: κ¹ Vol; Kostjuk: κ¹ Vol | |
| 40834 | 5.63 | bayer | κ² Vol | cross_index_curated | BSC: κ² Vol; HYG: κ² Vol; Kostjuk: κ² Vol | |
| 41211 | 5.61 | flamsteed | 1 Hya | cross_index_curated | BSC: 1 Hya; HYG: 1 Hya; Kostjuk: 1 Hya | |
| 41909 | 5.33 | bayer | η Cnc | cross_index_curated | BSC: η Cnc; HYG: η Cnc; Kostjuk: η Cnc | |
| 41909 | 5.33 | flamsteed | 33 Cnc | cross_index_curated | BSC: 33 Cnc; HYG: 33 Cnc; Kostjuk: 33 Cnc | |
| 42556 | 6.29 | bayer | ε Cnc | cross_index_curated | BSC: ε Cnc; HYG: ε Cnc; Kostjuk: ε Cnc; WGSN: ε Cnc | |
| 42556 | 6.29 | flamsteed | 41 Cnc | cross_index_curated | BSC: 41 Cnc; HYG: 41 Cnc; Kostjuk: 41 Cnc | |
| 43100 | 6.58 | bayer | ι Cnc | cross_index_curated | BSC: ι Cnc; HYG: ι Cnc; Kostjuk: ι Cnc | |
| 43100 | 6.58 | flamsteed | 48 Cnc | cross_index_curated | BSC: 48 Cnc; HYG: 48 Cnc; Kostjuk: 48 Cnc | |
| 43103 | 4.03 | bayer | ι Cnc | cross_index_curated | BSC: ι Cnc; HYG: ι Cnc; Kostjuk: ι Cnc; WGSN: ι Cnc | |
| 43103 | 4.03 | flamsteed | 48 Cnc | cross_index_curated | BSC: 48 Cnc; HYG: 48 Cnc; Kostjuk: 48 Cnc | |
| 43587 | 5.96 | bayer | ρ¹ Cnc | cross_index_curated | BSC: ρ¹ Cnc; HYG: ρ¹ Cnc; Kostjuk: ρ¹ Cnc | |
| 44154 | 5.23 | bayer | σ³ Cnc | cross_index_curated | BSC: σ³ Cnc; HYG: σ³ Cnc; Kostjuk: σ³ Cnc | |
| 44154 | 5.23 | flamsteed | 64 Cnc | cross_index_curated | BSC: 64 Cnc; HYG: 64 Cnc; Kostjuk: 64 Cnc | |
| 44838 | 7.35 | flamsteed |  | pending | Kostjuk: 74 Cnc | |
| 45170 | 6.49 | bayer |  | pending | BSC: π¹ Cnc; HYG: π¹ Cnc | |
| 45170 | 6.49 | flamsteed | 81 Cnc | cross_index_curated | BSC: 81 Cnc; HYG: 81 Cnc; Kostjuk: 81 Cnc | |
| 45811 | 4.8 | bayer |  | pending | Kostjuk: P Hya | |
| 45836 | 6.14 | flamsteed |  | pending | Kostjuk: 37 Lyn | |
| 47096 | 6.32 | flamsteed | 7 Leo | cross_index_curated | BSC: 7 Leo; HYG: 7 Leo; Kostjuk: 7 Leo | |
| 50414 | 5.25 | flamsteed | 22 Sex | cross_index_curated | BSC: 22 Sex; HYG: 22 Sex; Kostjuk: 22 Sex | |
| 51561 | 5.76 | bayer |  | pending | Kostjuk: s Vel | |
| 55846 | 6.49 | flamsteed | 83 Leo | cross_index_curated | BSC: 83 Leo; HYG: 83 Leo; Kostjuk: 83 Leo | |
| 58112 | 6.54 | flamsteed | 65 UMa | cross_index_curated | BSC: 65 UMa; HYG: 65 UMa; Kostjuk: 65 UMa | |
| 58117 | 7.03 | flamsteed | 65 UMa | cross_index_curated | BSC: 65 UMa; HYG: 65 UMa; Kostjuk: 65 UMa | |
| 58799 | 6.51 | flamsteed |  | pending | Kostjuk: 89 Cen | |
| 60891 | 6.63 | flamsteed |  | pending | Kostjuk: 17 Com | |
| 61136 | 5.49 | flamsteed |  | pending | Kostjuk: 35 Cru | |
| 61415 | 6.57 | flamsteed | 24 Com | cross_index_curated | BSC: 24 Com; HYG: 24 Com; Kostjuk: 24 Com | |
| 61418 | 5.03 | flamsteed | 24 Com | cross_index_curated | BSC: 24 Com; HYG: 24 Com; Kostjuk: 24 Com | |
| 61966 | 4.91 | flamsteed |  | pending | Kostjuk: 39 Cru; WGSN: 39 Cru | |
| 63003 | 4.03 | bayer | μ¹ Cru | cross_index_curated | BSC: μ¹ Cru; HYG: μ¹ Cru; Kostjuk: μ¹ Cru | |
| 63005 | 5.08 | bayer | μ² Cru | cross_index_curated | BSC: μ² Cru; HYG: μ² Cru; Kostjuk: μ² Cru | |
| 63121 | 5.61 | flamsteed | 12 CVn | cross_index_curated | BSC: 12 CVn; HYG: 12 CVn; Kostjuk: 12 CVn | |
| 63125 | 2.89 | flamsteed | 12 CVn | cross_index_curated | BSC: 12 CVn; HYG: 12 CVn; Kostjuk: 12 CVn | |
| 66465 | 7.05 | flamsteed |  | pending | HYG: 81 Vir | |
| 67275 | 4.5 | bayer | τ Boo | cross_index_curated | BSC: τ Boo; HYG: τ Boo; Kostjuk: τ Boo; WGSN: τ Boo | |
| 67275 | 4.5 | flamsteed | 4 Boo | cross_index_curated | BSC: 4 Boo; HYG: 4 Boo; Kostjuk: 4 Boo | |
| 67703 | 5.26 | bayer |  | pending | Kostjuk: N Cen | |
| 69483 | 4.53 | bayer | κ² Boo | cross_index_curated | BSC: κ² Boo; HYG: κ² Boo; Kostjuk: κ² Boo | |
| 69483 | 4.53 | flamsteed | 17 Boo | cross_index_curated | BSC: 17 Boo; HYG: 17 Boo; Kostjuk: 17 Boo | |
| 70497 | 4.04 | bayer | θ Boo | cross_index_curated | BSC: θ Boo; HYG: θ Boo; Kostjuk: θ Boo | |
| 70497 | 4.04 | flamsteed | 23 Boo | cross_index_curated | BSC: 23 Boo; HYG: 23 Boo; Kostjuk: 23 Boo | |
| 70890 | 11.01 | bayer |  | pending | WGSN: α Cen | |
| 73193 | 5.51 | bayer |  | pending | Kostjuk: M Ser | |
| 74824 | 4.07 | bayer | β Cir | cross_index_curated | BSC: β Cir; HYG: β Cir; Kostjuk: β Cir | |
| 75415 | 6.51 | bayer | μ² Boo | cross_index_curated | BSC: μ² Boo; HYG: μ² Boo; Kostjuk: μ² Boo | |
| 75415 | 6.51 | flamsteed | 51 Boo | cross_index_curated | BSC: 51 Boo; HYG: 51 Boo; Kostjuk: 51 Boo | |
| 75809 | 6.57 | bayer |  | pending | Kostjuk: π¹ UMi | |
| 75829 | 7.3 | bayer |  | pending | Kostjuk: π¹ UMi | |
| 78384 | 3.42 | bayer | η Lup | cross_index_curated | BSC: η Lup; HYG: η Lup; Kostjuk: η Lup | |
| 78661 | 5.73 | flamsteed |  | pending | Kostjuk: 18 UMi | |
| 78820 | 2.56 | bayer | β¹ Sco | cross_index_curated | BSC: β¹ Sco; HYG: β¹ Sco; Kostjuk: β¹ Sco; WGSN: β¹ Sco | |
| 78820 | 2.56 | flamsteed | 8 Sco | cross_index_curated | BSC: 8 Sco; HYG: 8 Sco; Kostjuk: 8 Sco | |
| 78821 | 4.9 | bayer | β² Sco | cross_index_curated | BSC: β² Sco; HYG: β² Sco; Kostjuk: β² Sco | |
| 78821 | 4.9 | flamsteed | 8 Sco | cross_index_curated | BSC: 8 Sco; HYG: 8 Sco; Kostjuk: 8 Sco | |
| 79043 | 5 | bayer | κ Her | cross_index_curated | BSC: κ Her; HYG: κ Her; Kostjuk: κ Her; WGSN: κ Her | |
| 79043 | 5 | flamsteed | 7 Her | cross_index_curated | BSC: 7 Her; HYG: 7 Her; Kostjuk: 7 Her | |
| 79045 | 6.25 | bayer | κ Her | cross_index_curated | BSC: κ Her; HYG: κ Her; Kostjuk: κ Her | |
| 79045 | 6.25 | flamsteed | 7 Her | cross_index_curated | BSC: 7 Her; HYG: 7 Her; Kostjuk: 7 Her | |
| 79490 | 6.03 | flamsteed |  | pending | Kostjuk: 39 Nor | |
| 79607 | 5.23 | bayer | σ CrB | cross_index_curated | BSC: σ CrB; HYG: σ CrB; Kostjuk: σ CrB | |
| 79607 | 5.23 | flamsteed | 17 CrB | cross_index_curated | BSC: 17 CrB; HYG: 17 CrB; Kostjuk: 17 CrB | |
| 80331 | 2.73 | bayer | η Dra | cross_index_curated | BSC: η Dra; HYG: η Dra; Kostjuk: η Dra; WGSN: η Dra | |
| 80331 | 2.73 | flamsteed | 14 Dra | cross_index_curated | BSC: 14 Dra; HYG: 14 Dra; Kostjuk: 14 Dra | |
| 81290 | 5.53 | flamsteed | 16 Dra | cross_index_curated | BSC: 16 Dra; HYG: 16 Dra; Kostjuk: 16 Dra | |
| 84500 | 5.89 | flamsteed |  | pending | Kostjuk: 38 Oph | |
| 84625 | 6.59 | bayer | ο Oph | cross_index_curated | BSC: ο Oph; HYG: ο Oph; Kostjuk: ο Oph | |
| 84625 | 6.59 | flamsteed | 39 Oph | cross_index_curated | BSC: 39 Oph; HYG: 39 Oph; Kostjuk: 39 Oph | |
| 84626 | 5.14 | bayer | ο Oph | cross_index_curated | BSC: ο Oph; HYG: ο Oph; Kostjuk: ο Oph | |
| 84626 | 5.14 | flamsteed | 39 Oph | cross_index_curated | BSC: 39 Oph; HYG: 39 Oph; Kostjuk: 39 Oph | |
| 85829 | 4.86 | bayer | ν² Dra | cross_index_curated | BSC: ν² Dra; HYG: ν² Dra; Kostjuk: ν² Dra | |
| 85998 | 5.8 | bayer |  | pending | Kostjuk: f Oph | |
| 85998 | 5.8 | flamsteed | 53 Oph | cross_index_curated | BSC: 53 Oph; HYG: 53 Oph; Kostjuk: 53 Oph | |
| 86614 | 4.57 | bayer | ψ¹ Dra | cross_index_curated | BSC: ψ¹ Dra; HYG: ψ¹ Dra; Kostjuk: ψ Dra; WGSN: ψ¹ Dra | |
| 86614 | 4.57 | flamsteed | 31 Dra | cross_index_curated | BSC: 31 Dra; HYG: 31 Dra; Kostjuk: 31 Dra | |
| 86620 | 5.81 | bayer |  | pending | BSC: ψ¹ Dra; HYG: ψ¹ Dra; Kostjuk: ψ Dra | |
| 86620 | 5.81 | flamsteed | 31 Dra | cross_index_curated | BSC: 31 Dra; HYG: 31 Dra; Kostjuk: 31 Dra | |
| 86831 | 6.16 | flamsteed | 61 Oph | cross_index_curated | BSC: 61 Oph; HYG: 61 Oph; Kostjuk: 61 Oph | |
| 86974 | 3.42 | flamsteed | 86 Her | cross_index_curated | BSC: 86 Her; HYG: 86 Her; Kostjuk: 86 Her | |
| 88817 | 5.79 | flamsteed | 100 Her | cross_index_curated | BSC: 100 Her; HYG: 100 Her; Kostjuk: 100 Her | |
| 88818 | 5.83 | flamsteed | 100 Her | cross_index_curated | BSC: 100 Her; HYG: 100 Her; Kostjuk: 100 Her | |
| 91919 | 4.67 | bayer | ε¹ Lyr | cross_index_curated | BSC: ε¹ Lyr; HYG: ε¹ Lyr; Kostjuk: ε¹ Lyr; WGSN: ε¹ Lyr | |
| 92117 | 5.89 | flamsteed | 5 Aql | cross_index_curated | BSC: 5 Aql; HYG: 5 Aql; Kostjuk: 5 Aql | |
| 92204 | 7.19 | flamsteed |  | pending | Kostjuk: 205 Dra | |
| 92226 | 5.2 | bayer | μ CrA | cross_index_curated | BSC: μ CrA; HYG: μ CrA; Kostjuk: μ CrA | |
| 92480 | 6.29 | flamsteed | 30 Sgr | cross_index_curated | BSC: 30 Sgr; HYG: 30 Sgr; Kostjuk: 30 Sgr | |
| 92946 | 4.62 | bayer | θ¹ Ser | cross_index_curated | BSC: θ¹ Ser; HYG: θ¹ Ser; Kostjuk: θ¹ Ser; WGSN: θ¹ Ser | |
| 92946 | 4.62 | flamsteed | 63 Ser | cross_index_curated | BSC: 63 Ser; HYG: 63 Ser; Kostjuk: 63 Ser | |
| 92951 | 4.98 | bayer | θ² Ser | cross_index_curated | BSC: θ² Ser; HYG: θ² Ser; Kostjuk: θ² Ser | |
| 92951 | 4.98 | flamsteed | 63 Ser | cross_index_curated | BSC: 63 Ser; HYG: 63 Ser; Kostjuk: 63 Ser | |
| 95241 | 3.96 | bayer | β¹ Sgr | cross_index_curated | BSC: β¹ Sgr; HYG: β¹ Sgr; Kostjuk: β¹ Sgr; WGSN: β¹ Sgr | |
| 95947 | 3.05 | bayer | β¹ Cyg | cross_index_curated | BSC: β¹ Cyg; HYG: β¹ Cyg; Kostjuk: β¹ Cyg; WGSN: β Cyg | |
| 95947 | 3.05 | flamsteed | 6 Cyg | cross_index_curated | BSC: 6 Cyg; HYG: 6 Cyg; Kostjuk: 6 Cyg | |
| 95951 | 5.12 | bayer | β² Cyg | cross_index_curated | BSC: β² Cyg; HYG: β² Cyg; Kostjuk: β² Cyg | |
| 95951 | 5.12 | flamsteed | 6 Cyg | cross_index_curated | BSC: 6 Cyg; HYG: 6 Cyg; Kostjuk: 6 Cyg | |
| 96895 | 5.99 | bayer |  | pending | Kostjuk: c Cyg | |
| 96895 | 5.99 | flamsteed | 16 Cyg | cross_index_curated | BSC: 16 Cyg; HYG: 16 Cyg; Kostjuk: 16 Cyg | |
| 96901 | 6.25 | bayer |  | pending | Kostjuk: c Cyg | |
| 96901 | 6.25 | flamsteed |  | pending | Kostjuk: 16 Cyg | |
| 97966 | 5.7 | flamsteed | 57 Aql | cross_index_curated | BSC: 57 Aql; HYG: 57 Aql; Kostjuk: 57 Aql | |
| 97967 | 6.49 | flamsteed | 57 Aql | cross_index_curated | BSC: 57 Aql; HYG: 57 Aql; Kostjuk: 57 Aql | |
| 98036 | 3.71 | bayer | β Aql | cross_index_curated | BSC: β Aql; HYG: β Aql; Kostjuk: β Aql; WGSN: β Aql | |
| 98036 | 3.71 | flamsteed | 60 Aql | cross_index_curated | BSC: 60 Aql; HYG: 60 Aql; Kostjuk: 60 Aql | |
| 100044 | 4.77 | bayer |  | pending | Kostjuk: P Cyg | |
| 100325 | 6.09 | bayer |  | pending | Kostjuk: β² Cap | |
| 100345 | 3.05 | bayer | β Cap | cross_index_curated | BSC: β Cap; HYG: β Cap; Kostjuk: β Cap; WGSN: β¹ Cap | |
| 100345 | 3.05 | flamsteed | 9 Cap | cross_index_curated | BSC: 9 Cap; HYG: 9 Cap; Kostjuk: 9 Cap | |
| 101123 | 5.94 | bayer | ο Cap | cross_index_curated | BSC: ο Cap; HYG: ο Cap; Kostjuk: ο Cap | |
| 101123 | 5.94 | flamsteed | 12 Cap | cross_index_curated | BSC: 12 Cap; HYG: 12 Cap; Kostjuk: 12 Cap | |
| 101589 | 4.64 | bayer | ζ Del | cross_index_curated | BSC: ζ Del; HYG: ζ Del; Kostjuk: ζ Del | |
| 101589 | 4.64 | flamsteed | 4 Del | cross_index_curated | BSC: 4 Del; HYG: 4 Del; Kostjuk: 4 Del | |
| 102125 | 6.51 | bayer | μ² Oct | cross_index_curated | BSC: μ² Oct; HYG: μ² Oct; Kostjuk: μ² Oct | |
| 102431 | 4.52 | bayer |  | pending | Kostjuk: υ¹ Cep | |
| 102531 | 5.15 | bayer | γ¹ Del | cross_index_curated | BSC: γ¹ Del; HYG: γ¹ Del; Kostjuk: γ¹ Del; WGSN: γ¹ Del | |
| 102531 | 5.15 | flamsteed | 12 Del | cross_index_curated | BSC: 12 Del; HYG: 12 Del; Kostjuk: 12 Del | |
| 102532 | 4.27 | bayer | γ² Del | cross_index_curated | BSC: γ² Del; HYG: γ² Del; Kostjuk: γ² Del | |
| 102532 | 4.27 | flamsteed | 12 Del | cross_index_curated | BSC: 12 Del; HYG: 12 Del; Kostjuk: 12 Del | |
| 104214 | 5.2 | flamsteed | 61 Cyg | cross_index_curated | BSC: 61 Cyg; HYG: 61 Cyg; Kostjuk: 61 Cyg | |
| 104217 | 6.05 | flamsteed | 61 Cyg | cross_index_curated | BSC: 61 Cyg; HYG: 61 Cyg; Kostjuk: 61 Cyg | |
| 106032 | 3.23 | bayer | β Cep | cross_index_curated | BSC: β Cep; HYG: β Cep; Kostjuk: β Cep; WGSN: β Cep | |
| 106032 | 3.23 | flamsteed | 8 Cep | cross_index_curated | BSC: 8 Cep; HYG: 8 Cep; Kostjuk: 8 Cep | |
| 106781 | 7.66 | flamsteed |  | pending | HYG: 3 Peg | |
| 110988 | 6.31 | bayer |  | pending | Kostjuk: δ Cep | |
| 110988 | 6.31 | flamsteed |  | pending | Kostjuk: 27 Cep | |
| 111544 | 6.6 | flamsteed | 8 Lac | cross_index_curated | BSC: 8 Lac; HYG: 8 Lac; Kostjuk: 8 Lac | |
| 111546 | 5.73 | flamsteed |  | pending | Kostjuk: 8 Lac | |
| 113191 | 7.04 | bayer |  | pending | Kostjuk: τ² Gru | |
| 113281 | 5.6 | flamsteed | 16 Lac | cross_index_curated | BSC: 16 Lac; HYG: 16 Lac; Kostjuk: 16 Lac | |
| 115126 | 5.2 | flamsteed | 94 Aqr | cross_index_curated | BSC: 94 Aqr; HYG: 94 Aqr; Kostjuk: 94 Aqr | |
| 115271 | 5.58 | flamsteed | 63 Peg | cross_index_curated | BSC: 63 Peg; HYG: 63 Peg; Kostjuk: 63 Peg | |
| 116904 | 8.52 | bayer |  | pending | Kostjuk: A² Aqr | |
| 116904 | 8.52 | flamsteed |  | pending | Kostjuk: 104 Aqr | |
| 117756 | 5.76 | bayer |  | pending | Kostjuk: h Aqr | |

## Existing-kind variants: preserve Wikidata pending review

| HIP | V (Hipparcos) | Kind | Wikidata | Other candidates | Source values | Selman |
| ---: | ---: | --- | --- | --- | --- | --- |
| 8832 | 3.88 | bayer | γ Ari | γ1 Ari, γ2 Ari | BSC: γ2 Ari; HYG: γ2 Ari; Kostjuk: γ1 Ari | |
| 9347 | 3.99 | bayer | υ1 Cet | υ Cet | BSC: υ Cet; HYG: υ Cet; Kostjuk: υ Cet | |
| 9640 | 2.1 | bayer | γ And | γ1 And | BSC: γ1 And; HYG: γ1 And; Kostjuk: γ1 And; WGSN: γ And | |
| 13702 | 5.58 | bayer | ρ3 Ari | ρ Ari | BSC: ρ3 Ari; HYG: ρ3 Ari; Kostjuk: ρ Ari | |
| 13847 | 2.88 | bayer | θ Eri | θ1 Eri | BSC: θ1 Eri; HYG: θ1 Eri; Kostjuk: θ1 Eri; WGSN: θ1 Eri | |
| 15457 | 4.84 | bayer | κ1 Cet | κ Cet | BSC: κ1 Cet; HYG: κ1 Cet; Kostjuk: κ Cet | |
| 15627 | 5.27 | bayer | τ1 Ari | τ Ari | BSC: τ1 Ari; HYG: τ1 Ari; Kostjuk: τ Ari | |
| 19990 | 4.93 | bayer | ω2 Tau | ω Tau | BSC: ω2 Tau; HYG: ω2 Tau; Kostjuk: ω Tau | |
| 20455 | 3.77 | bayer | δ1 Tau | δ Tau | BSC: δ1 Tau; HYG: δ1 Tau; Kostjuk: δ Tau; WGSN: δ1 Tau | |
| 20635 | 4.21 | bayer | κ1 Tau | κ Tau | BSC: κ1 Tau; HYG: κ1 Tau; Kostjuk: κ Tau | |
| 21589 | 4.27 | bayer | c Tau | c1 Tau | Kostjuk: c1 Tau | |
| 23595 | 4.55 | bayer | γ1 Cae | γ Cae | BSC: γ1 Cae; HYG: γ1 Cae; Kostjuk: γ Cae | |
| 23596 | 6.32 | bayer | γ2 Cae | γ Cae | BSC: γ2 Cae; HYG: γ2 Cae; Kostjuk: γ Cae | |
| 25473 | 4.59 | bayer | ψ2 Ori | ψ Ori | BSC: ψ2 Ori; HYG: ψ2 Ori; Kostjuk: ψ Ori | |
| 36363 | 5.41 | bayer | y1 Pup | y Pup | Kostjuk: y Pup | |
| 37229 | 3.8 | bayer | k Pup | κ1 Pup | Kostjuk: κ1 Pup | |
| 39191 | 5.87 | bayer | ω1 Cnc | ω Cnc | BSC: ω1 Cnc; HYG: ω1 Cnc; Kostjuk: ω Cnc | |
| 39780 | 5.3 | bayer | μ2 Cnc | μ Cnc | BSC: μ2 Cnc; HYG: μ2 Cnc; Kostjuk: μ Cnc | |
| 39953 | 1.75 | bayer | γ Vel | γ2 Vel | BSC: γ2 Vel; HYG: γ2 Vel; Kostjuk: γ2 Vel | |
| 40023 | 5.73 | bayer | ψ2 Cnc | ψ Cnc | BSC: ψ Cnc; HYG: ψ Cnc; Kostjuk: ψ Cnc | |
| 40167 | 4.67 | bayer | ζ Cnc | ζ1 Cnc, ζ2 Cnc | BSC: ζ2 Cnc; HYG: ζ2 Cnc; Kostjuk: ζ1 Cnc, ζ2 Cnc; WGSN: ζ Cnc | |
| 45410 | 5.36 | bayer | π2 Cnc | π Cnc | BSC: π2 Cnc; HYG: π2 Cnc; Kostjuk: π Cnc | |
| 48552 | 6.72 | flamsteed | 9 Sex | 8 Sex | HYG: 8 Sex; Kostjuk: 9 Sex | |
| 49065 | 5.53 | bayer | μ1 Cha | μ Cha | BSC: μ1 Cha; HYG: μ1 Cha; Kostjuk: μ Cha | |
| 50583 | 2.01 | bayer | γ Leo | γ1 Leo | BSC: γ1 Leo; HYG: γ1 Leo; Kostjuk: γ1 Leo; WGSN: γ1 Leo | |
| 52085 | 4.91 | bayer | φ3 Hya | φ Hya | BSC: φ3 Hya; HYG: φ3 Hya; Kostjuk: φ Hya | |
| 54301 | 4.62 | bayer | z1 Car | z Car | Kostjuk: z Car | |
| 60718 | 0.77 | bayer | α Cru | α1 Cru | BSC: α1 Cru; HYG: α1 Cru; Kostjuk: α1 Cru; WGSN: α Cru | |
| 69481 | 6.62 | bayer | κ Boo | κ1 Boo | BSC: κ1 Boo; HYG: κ1 Boo; Kostjuk: κ1 Boo | |
| 71500 | 5.39 | bayer | A Lup | a Lup | Kostjuk: a Lup | |
| 71681 | 1.35 | bayer | α2 Cen | α Cen | BSC: α2 Cen; HYG: α2 Cen; Kostjuk: α Cen; WGSN: α Cen | |
| 71762 | 4.49 | bayer | π Boo | π1 Boo | BSC: π1 Boo; HYG: π1 Boo; Kostjuk: π1 Boo | |
| 74392 | 4.54 | bayer | ι1 Lib | ι Lib | BSC: ι1 Lib; HYG: ι1 Lib; Kostjuk: ι Lib | |
| 75411 | 4.31 | bayer | μ Boo | μ1 Boo | BSC: μ1 Boo; HYG: μ1 Boo; Kostjuk: μ1 Boo; WGSN: μ Boo | |
| 76126 | 5.53 | bayer | ζ4 Lib | ζ Lib | BSC: ζ4 Lib; HYG: ζ4 Lib; Kostjuk: ζ Lib | |
| 76669 | 4.64 | bayer | ζ CrB, ζ2 CrB | ζ1 CrB | BSC: ζ1 CrB; HYG: ζ1 CrB; Kostjuk: ζ1 CrB, ζ2 CrB | |
| 81710 | 5.89 | bayer | η TrA | η1 TrA | BSC: η1 TrA; HYG: η1 TrA; Kostjuk: η1 TrA | |
| 84345 | 2.78 | bayer | α Her | α1 Her | BSC: α1 Her; HYG: α1 Her; Kostjuk: α1 Her; WGSN: α1 Her | |
| 86974 | 3.42 | bayer | μ1 Her | μ Her | BSC: μ Her; HYG: μ Her; Kostjuk: μ Her | |
| 87314 | 5.68 | bayer | ν1 Ara | υ1 Ara | Kostjuk: υ1 Ara | |
| 87379 | 6.09 | bayer | ν2 Ara | υ2 Ara | Kostjuk: υ2 Ara | |
| 88635 | 2.98 | bayer | γ2 Sgr | γ Sgr | BSC: γ2 Sgr; HYG: γ2 Sgr; Kostjuk: γ Sgr; WGSN: γ2 Sgr | |
| 89153 | 4.96 | flamsteed | 1 Sgr | 11 Sgr | BSC: 11 Sgr; HYG: 1 Sgr; Kostjuk: 11 Sgr | |
| 90968 | 5.67 | bayer | κ2 CrA | κ1 CrA | BSC: κ1 CrA; HYG: κ1 CrA; Kostjuk: κ2 CrA | |
| 90969 | 6.31 | bayer | κ1 CrA | κ2 CrA | BSC: κ2 CrA; HYG: κ2 CrA; Kostjuk: κ1 CrA | |
| 91926 | 4.59 | bayer | ε Lyr | ε2 Lyr | BSC: ε2 Lyr; HYG: ε2 Lyr; Kostjuk: ε2 Lyr | |
| 92405 | 5.22 | bayer | ν2 Lyr | ν Lyr | BSC: ν2 Lyr; HYG: ν2 Lyr; Kostjuk: ν Lyr | |
| 95853 | 3.76 | bayer | ι2 Cyg | ι Cyg | BSC: ι2 Cyg; HYG: ι2 Cyg; Kostjuk: ι Cyg | |
| 98162 | 4.54 | bayer | b Sgr | b1 Sgr | Kostjuk: b1 Sgr | |
| 101923 | 5.24 | bayer | τ2 Cap | τ Cap | BSC: τ Cap; HYG: τ Cap; Kostjuk: τ Cap | |
| 107310 | 4.49 | bayer | μ Cyg | μ1 Cyg | BSC: μ1 Cyg; HYG: μ1 Cyg; Kostjuk: μ1 Cyg | |
| 107382 | 5.1 | bayer | c1 Cap | c Cap | Kostjuk: c Cap | |
| 108478 | 6.13 | bayer | κ1 Ind | κ Ind | BSC: κ1 Ind; HYG: κ1 Ind; Kostjuk: κ Ind | |
| 109081 | 5.62 | bayer | κ2 Ind | κ Ind | BSC: κ2 Ind; HYG: κ2 Ind; Kostjuk: κ Ind | |
| 109410 | 4.28 | bayer | π2 Peg | π Peg | BSC: π2 Peg; HYG: π2 Peg; Kostjuk: π Peg; WGSN: π2 Peg | |
| 110960 | 3.65 | bayer | ζ Aqr | ζ1 Aqr | BSC: ζ1 Aqr; HYG: ζ1 Aqr; Kostjuk: ζ1 Aqr | |
| 111056 | 5.45 | bayer | ρ2 Cep | ρ Cep | BSC: ρ2 Cep; HYG: ρ2 Cep; Kostjuk: ρ Cep | |
| 112211 | 4.68 | bayer | g1 Aqr | g Aqr | Kostjuk: g Aqr | |

## Review categories

Case 1 describes close components that overlap at the chosen chart scale.
Case 2 is a singleton numeric index in the compared HIP cross-indexes; absence
of another HIP association does not establish that the other indexed star
is absent. Case 3 is a family containing three or more distinct numeric
indices. These categories overlap and do not assert physical binding.

No superscript is removed and no brightest-component choice is made by this
stage. `β Sco` remains a system alias with two HIP matches; explicit
`β¹ Sco` and `β² Sco` distinguish HIP 78820 and 78821.

## Source provenance

- [bsc-catalog.gz](https://cdsarc.cds.unistra.fr/ftp/V/50/catalog.gz): acquired 2026-10-05T22:54:35.804528+00:00; SHA-256 `3dc44b1e90be8fbe5bcc7656032560f51275f985c7e3f783c9028e1838ec7bed`.
- [hyg-v44.csv.gz](https://codeberg.org/astronexus/hyg/media/commit/53e3df311869e813ace5f1ad2ec4ce909f13256c/data/hyg/CURRENT/hyg_v44.csv.gz): acquired 2026-10-05T23:04:17.623477+00:00; SHA-256 `00b349893b9a53106dd488d8371e8d2fa586043e500bb3cdb8bff3931682197d`.
- [kostjuk-catalog.dat](https://cdsarc.cds.unistra.fr/ftp/IV/27A/catalog.dat): acquired 2026-10-05T22:53:26.361047+00:00; SHA-256 `bc2292ddad544c1daefe8f12c6ed47a051006632d84e4a03b36d41f07d626289`.
- [wgsn-current.html](https://exopla.net/star-names/modern-iau-star-names/): acquired 2026-10-05T22:55:16.779255+00:00; SHA-256 `f8bbf4dd911cbcf60b5b32fa8c68c3ffb6d7d15b261fdc69d259cf962d4b0203`.
- [wikidata-designations.json](https://query.wikidata.org/sparql?query=SELECT+%3Fitem+%3Flabel+%3Fstatement+%3Fcode+%3Fcatalog+%3Frank+%3Fhipstatement+%3Fhip+%3Fhiprank+%3Freference+WHERE+%7B%0A+VALUES+%3Fcatalog+%7B+wd%3AQ105616+wd%3AQ111116+%7D%0A+%3Fitem+p%3AP528+%3Fstatement+.+%3Fstatement+ps%3AP528+%3Fcode%3B+pq%3AP972+%3Fcatalog%3B+wikibase%3Arank+%3Frank+.%0A+OPTIONAL+%7B+%3Fitem+p%3AP528+%3Fhipstatement+.+%3Fhipstatement+ps%3AP528+%3Fhip%3B+pq%3AP972+wd%3AQ537199%3B+wikibase%3Arank+%3Fhiprank+.+%7D%0A+OPTIONAL+%7B+%3Fstatement+prov%3AwasDerivedFrom+%3Freference+.+%7D%0A+OPTIONAL+%7B+%3Fitem+rdfs%3Alabel+%3Flabel+.+FILTER%28LANG%28%3Flabel%29%3D%22en%22%29+%7D%0A%7D&format=json): acquired 2026-10-05T22:58:45.513515+00:00; SHA-256 `a341c42bb1dc4739c26634fc92f475ebd880254deb55851e0c4c12ee2b4a2697`.
