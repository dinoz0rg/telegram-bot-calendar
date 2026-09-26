from __future__ import annotations

from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from telegram_bot_calendar import callback as cb
from telegram_bot_calendar import is_calendar_callback, new_session

ids = st.one_of(st.integers(0, 10**6).map(str), st.text("abcXYZ09-", min_size=1, max_size=8))
dates = st.dates(date(1, 1, 1), date(9999, 12, 31))
sessions = st.one_of(st.none(), st.text("abcdefABC0123456789", min_size=1, max_size=8))


@given(
    ids,
    st.sampled_from([a for a in cb.ACTIONS if a != cb.NOTHING]),
    st.sampled_from(cb.STEPS),
    dates,
    st.one_of(st.none(), dates),
    sessions,
    st.one_of(st.none(), st.integers(1, 10**18)),
)
def test_round_trip(
    cid: str, action: str, step: str, day: date, start: date | None, session: str | None, salt: int | None
) -> None:
    p = cb.Payload(cid, action, step, day, start, session)
    data = cb.encode(p, salt)
    assert len(data.encode()) <= cb.LIMIT
    assert cb.decode(data, cid) == p
    assert is_calendar_callback(data, cid)


@given(st.one_of(st.text(max_size=80), st.binary(max_size=80), st.none(), st.integers()))
def test_decode_never_raises(data: object) -> None:
    cb.decode(data, 0)


def test_format() -> None:
    p = cb.Payload("0", cb.SELECT, cb.DAY, date(2024, 6, 5))
    assert cb.encode(p) == "cbcal_0_s_d_2024_6_5"
    assert cb.encode(cb.Payload("0", cb.NOTHING, cb.DAY, date(2024, 6, 5), session="ab")) == "cbcal_0_n"


def test_too_long_raises() -> None:
    with pytest.raises(ValueError, match="64 bytes"):
        cb.encode(cb.Payload("z" * 60, cb.SELECT, cb.DAY, date(2024, 1, 1)))


@pytest.mark.parametrize(
    "data",
    [
        None,
        "",
        "hello",
        "cbcal",
        "cbcal_0",
        "cbcal_1_s_d_2021_1_1",
        "cbcal_0_z_d_2021_1_1",
        "cbcal_0_s_d_2021_2_30",
        "cbcal_0_s_d_2021_13_1",
        "cbcal_0_s_d_2021_1_1_junk",
        "cbcal_0_s_d_x_y_z",
        "cbcal_0_s_d_2021_1_1_r20211301",
        "cbcal_0_s_d_٢٠٢١_1_1",
        b"\xff\xfe",
        123,
    ],
)
def test_decode_rejects(data: object) -> None:
    assert cb.decode(data, 0) is None


def test_foreign_id_is_not_ours() -> None:
    assert not is_calendar_callback("cbcal_12_s_d_2021_1_1", 1)
    assert is_calendar_callback(b"cbcal_1_n", 1)
    assert not is_calendar_callback(None)


def test_new_session_is_valid() -> None:
    assert cb.valid_session(new_session())
