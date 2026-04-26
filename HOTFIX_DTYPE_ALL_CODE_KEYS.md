# Hotfix: normalize all fund code keys

Fixed recurring Render/Pandas errors:

```text
ValueError: You are trying to merge on int64 and str columns for key 'code'
ValueError: You are trying to merge on int64 and str columns for key '基金代码'
```

Changes:
- `fund_advisor/data_provider.py`: reads `code` as string and zero-pads it at source.
- `fund_advisor/lookthrough.py`: normalizes recommendation and holding codes before merge/filter.
- `app.py`: normalizes `基金代码` and `code` before preference merge.

After uploading these changes to GitHub, redeploy Render from the latest commit.
