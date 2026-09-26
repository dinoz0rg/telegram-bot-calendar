# Changelog

## 2.3.0 — 2026-09-27

- `mark_today=True` now shows today as a plain number on a coloured button (Bot API `style`, blue `"primary"` by default) instead of `•15`. It applies to the day grid and the range day views. Selected-range markers are unchanged.
- `Style.today_style`: `"primary"`, `"success"`, `"danger"` or `None`. For the old look use `Style(today="•{day}", today_style=None)`.
- Telethon buttons have no style, so there today keeps the `•` prefix.
- Range picker: the start day, end day and every day between are plain numbers on `"primary"` buttons, so the span reads as one solid bar. Selection wins over today's style. Confirm is `"✓ Confirm"` on a green `"success"` button; Change is unstyled. Callback data is unchanged.
- New `Style.selected_style`, `Style.in_range_style` (default `"primary"`) and `Style.confirm_style` (default `"success"`), validated like `today_style`. For the old look use `Style(selected="[{day}]", in_range="·{day}·", confirm="Confirm", selected_style=None, in_range_style=None, confirm_style=None)`. On Telethon, styled range days and Confirm get the `•` prefix.
- Buttons get a `"style"` key only when styled, so all other JSON output and all callback data are unchanged.

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
