#!/usr/bin/env python3
"""Extrae valores de widgets AcroForm de un PDF a JSON normalizado."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pikepdf


def _get_field_name(annot: object) -> str:
    parts: list[str] = []
    obj = annot
    while obj is not None:
        t = obj.get("/T")
        if t is not None:
            parts.append(str(t))
        obj = obj.get("/Parent")
    parts.reverse()
    return ".".join(parts) if parts else ""


def _get_field_type(annot: object) -> str:
    ft = annot.get("/FT")
    if ft is None:
        parent = annot.get("/Parent")
        if parent is not None:
            ft = parent.get("/FT")
    return str(ft) if ft is not None else ""


def _decode_value(raw_val: object | None) -> str:
    if raw_val is None:
        return ""

    def safe_text(value: object) -> str:
        try:
            return str(value)
        except Exception:
            try:
                return bytes(value).decode("latin-1", errors="replace")
            except Exception:
                return repr(value)

    if isinstance(raw_val, pikepdf.Name):
        return safe_text(raw_val).lstrip("/")

    text = safe_text(raw_val)

    if text.startswith("<") and text.endswith(">"):
        hex_data = text[1:-1]
        if hex_data and all(ch in "0123456789abcdefABCDEF" for ch in hex_data):
            try:
                return bytes.fromhex(hex_data).decode("cp1252")
            except Exception:
                return text

    if text.startswith("(") and text.endswith(")"):
        return text[1:-1]

    return text


def extract_pdf_fields(pdf_path: Path) -> dict[str, dict[str, str]]:
    pdf = pikepdf.open(str(pdf_path))
    out: dict[str, dict[str, str]] = {}

    for page_index, page in enumerate(pdf.pages, start=1):
        annots = page.get("/Annots")
        if annots is None:
            continue

        for annot in annots:
            if annot.get("/Subtype") != pikepdf.Name("/Widget"):
                continue

            name = _get_field_name(annot)
            if not name:
                continue

            ftype = _get_field_type(annot)
            raw_v = annot.get("/V")
            raw_as = annot.get("/AS")

            out[name] = {
                "field_type": ftype,
                "value": _decode_value(raw_v),
                "appearance_state": _decode_value(raw_as),
                "page": str(page_index),
            }

    pdf.close()
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrae widgets de PDF a JSON")
    parser.add_argument("pdf", type=Path, help="Ruta al PDF")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Ruta de salida JSON (por defecto: stdout)",
    )
    args = parser.parse_args()

    data = extract_pdf_fields(args.pdf)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Campos extraidos: {len(data)}")
        print(f"JSON guardado en: {args.output}")
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
