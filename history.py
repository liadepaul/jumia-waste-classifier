"""Session history helpers for EcoSort analyses."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime
from io import StringIO
from typing import Any

import streamlit as st


HISTORY_KEY = "analysis_history"
MAX_HISTORY_ITEMS = 30


@dataclass(frozen=True)
class HistoryEntry:
    date: str
    source: str
    item: str
    material: str
    bin_label: str
    confidence: str
    ecoscore: int
    advice: str


def get_history() -> list[dict[str, Any]]:
    return list(st.session_state.get(HISTORY_KEY, []))


def add_history_entry(
    source: str,
    item: str,
    material: str | None,
    bin_label: str,
    confidence: float | None,
    ecoscore: int,
    advice: str,
) -> None:
    signature = f"{source}|{item}|{material}|{bin_label}|{confidence}|{ecoscore}"
    if st.session_state.get("last_history_signature") == signature:
        return

    entry = HistoryEntry(
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        source=source,
        item=item,
        material=material or "non determinee",
        bin_label=bin_label,
        confidence=f"{confidence:.1%}" if confidence is not None else "non disponible",
        ecoscore=int(ecoscore),
        advice=advice,
    )
    history = [asdict(entry), *get_history()]
    st.session_state[HISTORY_KEY] = history[:MAX_HISTORY_ITEMS]
    st.session_state["last_history_signature"] = signature


def history_to_csv(history: list[dict[str, Any]]) -> bytes:
    output = StringIO()
    fieldnames = ["date", "source", "item", "material", "bin_label", "confidence", "ecoscore", "advice"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for entry in history:
        writer.writerow({field: entry.get(field, "") for field in fieldnames})
    return output.getvalue().encode("utf-8-sig")
