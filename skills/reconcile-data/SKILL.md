---
name: reconcile-data
description: Reconcile exports and build repeatable data transformations. Use for Postgres or Snowflake extracts, CSV files, Pandas pipelines and Excel reconciliation reports.
---

# Reconcile data

1. Obtain authorized inputs and define the join key, grain, date range, time zone, units, currency and expected output. Inspect schemas without printing sensitive row values.
2. Preserve raw input files. Normalize column names explicitly; retain original columns or record the mapping. Keep identifiers as strings where leading zeros matter.
3. Check missing keys and duplicate keys before joining. Measure expected cardinality and stop on unexplained many-to-many expansion.
4. Preserve null versus zero, distinguish unmatched rows on each side, and use explicit decimal or integer-minor-unit arithmetic for monetary totals.
5. Produce matched, left-only, right-only and mismatched outputs plus row counts and control totals. Never silently drop rejected rows.
6. For database work start with bounded read-only queries. Do not execute write statements without task authorization. Validate workbook formulas and formatting when exporting a spreadsheet.
7. Report input fingerprints, transformation rules, reconciliation totals and unresolved discrepancies. Use synthetic fixtures in public examples.

Example request: Compare two supplier exports without losing unmatched SKUs or duplicating totals.
