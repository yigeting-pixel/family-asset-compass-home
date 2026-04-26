# Hotfix: Render pandas merge dtype error

Fixed error:

```text
ValueError: You are trying to merge on int64 and str columns for key '基金代码'
```

Cause: Render/Pandas inferred fund code columns differently across CSV-derived tables.

Fix:
- Normalize `recommendations["基金代码"]` and `pref_map["code"]` to zero-padded strings before merge.
- Harden `fund_preferences.py` code normalization.
