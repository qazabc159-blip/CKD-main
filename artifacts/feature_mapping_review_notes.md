# Feature Mapping Review Notes (v1)

This file records the manual review decisions that were previously left to the researcher.

## Approved v1 shared schema
The following **23 exact-name cross-dataset features** are retained for the first shared model schema:

- age
- sg
- al
- su
- rbc
- pc
- pcc
- ba
- bgr
- bu
- sc
- sod
- pot
- hemo
- pcv
- wbcc
- rbcc
- htn
- dm
- cad
- appet
- pe
- ane

## Explicit exclusions
- `bp` (#336) vs `bp (Diastolic)` (#857): **excluded in v1** because the equivalence is not sufficiently defensible.
- `affected`, `bp limit`, `grf`, `stage` (#857 only): **excluded in v1** because they have no approved shared counterpart in #336.

## Why this is the right first decision
This conservative schema keeps the first binary-classification experiment clean and defensible.  
A second-round value audit can later revisit category codings and consider whether any excluded fields deserve a justified harmonization rule.
