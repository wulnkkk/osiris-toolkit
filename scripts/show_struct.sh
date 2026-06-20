#!/bin/bash
BASE=/path/to/Zmaterial
for d in Au Au0 Ti Ti0 CH_fixed CH0_fixed; do
    echo "===== $d ====="
    echo "INPUT:"; ls $BASE/$d/*.in
    echo "MS:"; find $BASE/$d/MS -maxdepth 1 -type d
    for q in $(ls $BASE/$d/MS/FLD/); do echo "  fld/$q: $(ls $BASE/$d/MS/FLD/$q/*.zdf 2>/dev/null|wc -l)"; done
    for s in $(ls $BASE/$d/MS/DENSITY/ 2>/dev/null); do echo "  density/$s: $(ls $BASE/$d/MS/DENSITY/$s/*.zdf 2>/dev/null|wc -l)"; done
    for s in $(ls $BASE/$d/MS/PHA/ 2>/dev/null); do echo "  pha/$s: $(ls $BASE/$d/MS/PHA/$s/*.zdf 2>/dev/null|wc -l)"; done
    for t in field k_space scattering; do echo "  figures/$t: $(ls $BASE/$d/figures/$t/ 2>/dev/null|wc -l)"; done
    echo "--- run-info ---"; cat $BASE/$d/run-info 2>/dev/null
    echo ""
done
