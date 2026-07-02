"""Compila catálogos PO simples sem depender do GNU gettext."""

import ast
import struct
import sys
from pathlib import Path


def parse_po(path):
    entries = []
    entry = {}
    current = None
    for raw_line in path.read_text(encoding="utf-8").splitlines() + [""]:
        line = raw_line.strip()
        if not line:
            if "msgid" in entry and any(
                key.startswith("msgstr") for key in entry
            ):
                entries.append(entry)
            entry = {}
            current = None
            continue
        if line.startswith("#"):
            continue
        if line.startswith("msgid_plural "):
            current = "msgid_plural"
            entry[current] = ast.literal_eval(line[13:])
        elif line.startswith("msgid "):
            current = "msgid"
            entry[current] = ast.literal_eval(line[6:])
        elif line.startswith("msgstr["):
            index = int(line[7 : line.index("]")])
            current = f"msgstr_{index}"
            entry[current] = ast.literal_eval(line.split(None, 1)[1])
        elif line.startswith("msgstr "):
            current = "msgstr"
            entry[current] = ast.literal_eval(line[7:])
        elif line.startswith('"') and current:
            entry[current] += ast.literal_eval(line)

    messages = {}
    for item in entries:
        if "msgid_plural" in item:
            key = item["msgid"] + "\0" + item["msgid_plural"]
            value = item.get("msgstr_0", "") + "\0" + item.get(
                "msgstr_1", ""
            )
        else:
            key = item["msgid"]
            value = item["msgstr"]
        messages[key] = value
    return messages


def write_mo(messages, path):
    keys = sorted(messages)
    ids = [key.encode("utf-8") for key in keys]
    values = [messages[key].encode("utf-8") for key in keys]
    count = len(keys)
    key_table_offset = 28
    value_table_offset = key_table_offset + count * 8
    data_offset = value_table_offset + count * 8
    key_data = b""
    key_table = []
    for value in ids:
        key_table.append((len(value), data_offset + len(key_data)))
        key_data += value + b"\0"
    value_data_offset = data_offset + len(key_data)
    value_data = b""
    value_table = []
    for value in values:
        value_table.append((len(value), value_data_offset + len(value_data)))
        value_data += value + b"\0"
    output = struct.pack(
        "<7I",
        0x950412DE,
        0,
        count,
        key_table_offset,
        value_table_offset,
        0,
        0,
    )
    output += b"".join(struct.pack("<2I", *item) for item in key_table)
    output += b"".join(struct.pack("<2I", *item) for item in value_table)
    path.write_bytes(output + key_data + value_data)


source = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "locale/en/LC_MESSAGES/django.po"
)
write_mo(parse_po(source), source.with_suffix(".mo"))
