# X03 local threat-model review

Verdict: **engineering controls implemented; independent security review open**.

| Threat | Implemented S0/S1 control | Remaining control |
|---|---|---|
| Path traversal / junction | UUID case folders, allow-listed areas and filenames, resolved containment | Windows junction/reparse-point integration test |
| PHI in diagnostics | Event field allow-list; path, UID, control-character and identifier redaction | adversarial corpus and human audit |
| Mixed/wrong CT | explicit series UID; duplicate SOP, FoR, geometry and gap checks | enhanced multi-frame/transfer syntax fixtures |
| Malicious command input | argv tuple and `shell=False`; task/class map probed | subprocess ACL/sandbox and executable hash |
| Forged model result | required machine run report, complete masks, source/affine hashes | signed model manifest and weight SHA |
| Partial/corrupt output | `.partial`, per-file SHA256, atomic rename, tamper check | power-loss and antivirus-lock drill |
| Geometry mirroring | asymmetric marker and LPS↔RAS tests | Slicer MRML and independent SEG roundtrip |

