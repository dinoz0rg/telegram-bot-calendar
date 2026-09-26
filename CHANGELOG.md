# Changelog

## 2.2.0 — 2026-09-27

- Month+year and year labels follow CLDR per locale (for example `2026年5月`, `2026년 5월`, `2026. máj.`). This covers the nav titles, year buttons and range summary. `en`, `eo` and `ru` output is unchanged. Callback data is unchanged.
- `month_year_format` kwarg (for example `"{month} {year}"`) to set your own month+year label.
- `buddhist_era` kwarg: labels show the year +543. Callbacks and returned dates stay Gregorian.
- `rtl` kwarg: each button row is shown in reverse order.

## 2.1.0 — 2026-09-27

- `first_weekday` kwarg (0 Monday … 6 Sunday) on all calendars. The default is unchanged.
- 51 locales, generated from CLDR by `scripts/gen_locales.py`. `en`, `eo` and `ru` are unchanged.
- `month_names` and `weekday_names` kwargs for your own labels.
- README images use absolute URLs, so they show on PyPI. Project URLs and Python 3.9–3.13 classifiers.

## 2.0.0 — first release
