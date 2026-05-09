"""Repair common Claude-agent JSON formatting mistakes without rewriting content."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


KNOWN_ARRAY_FIELDS = {
    "actions",
    "author_input_needed",
    "evidence_coverage",
    "risks",
    "synchronized_updates",
    "visual_diagnosis",
}


def _is_escaped(text: str, index: int) -> bool:
    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def _last_unescaped_quote_before_suffix(line: str) -> int | None:
    suffix = re.search(r'"\s*,?\s*$', line)
    if not suffix:
        return None
    index = suffix.start()
    return index if not _is_escaped(line, index) else None


def _repair_inline_string_line(line: str) -> tuple[str, int]:
    match = re.match(r'^(\s*"[^"]+"\s*:\s*)"', line)
    if not match:
        return line, 0

    value_start = match.end() - 1
    value_end = _last_unescaped_quote_before_suffix(line)
    if value_end is None or value_end <= value_start:
        return line, 0

    content = line[value_start + 1 : value_end]
    repaired_chars: list[str] = []
    changes = 0
    for index, char in enumerate(content):
        if char == '"' and not _is_escaped(content, index):
            repaired_chars.append("”")
            changes += 1
        else:
            repaired_chars.append(char)

    if changes == 0:
        return line, 0
    return line[: value_start + 1] + "".join(repaired_chars) + line[value_end:], changes


def repair_unescaped_inline_quotes(text: str) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    repaired: list[str] = []
    changes = 0
    for line in lines:
        fixed, line_changes = _repair_inline_string_line(line)
        repaired.append(fixed)
        changes += line_changes
    return "".join(repaired), changes


def replace_known_null_arrays(value: Any) -> tuple[Any, int]:
    changes = 0
    if isinstance(value, dict):
        fixed: dict[str, Any] = {}
        for key, item in value.items():
            if key in KNOWN_ARRAY_FIELDS and item is None:
                fixed[key] = []
                changes += 1
            else:
                fixed_item, item_changes = replace_known_null_arrays(item)
                fixed[key] = fixed_item
                changes += item_changes
        return fixed, changes
    if isinstance(value, list):
        fixed_list = []
        for item in value:
            fixed_item, item_changes = replace_known_null_arrays(item)
            fixed_list.append(fixed_item)
            changes += item_changes
        return fixed_list, changes
    return value, 0


def validate_schema(data: Any, schema_path: Path) -> str | None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda err: list(err.path))
    if not errors:
        return None
    first = errors[0]
    path = "$" + "".join(f"[{part!r}]" if isinstance(part, int) else f".{part}" for part in first.path)
    return f"{path}: {first.message}"


def repair_common_agent_json(input_path: Path, output_path: Path, schema_path: Path | None = None) -> tuple[bool, str]:
    text = input_path.read_text(encoding="utf-8")
    repaired_text, quote_changes = repair_unescaped_inline_quotes(text)

    try:
        data = json.loads(repaired_text)
    except json.JSONDecodeError as exc:
        return False, f"JSON still invalid after common repair: {exc.msg} at line {exc.lineno} column {exc.colno}"

    data, null_array_changes = replace_known_null_arrays(data)
    if schema_path:
        schema_error = validate_schema(data, schema_path)
        if schema_error:
            return False, f"Schema still invalid after common repair: {schema_error}"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True, f"repaired quote_changes={quote_changes} null_array_changes={null_array_changes}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair common agent JSON syntax/schema mistakes.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--schema")
    args = parser.parse_args()

    ok, message = repair_common_agent_json(
        Path(args.input),
        Path(args.output),
        Path(args.schema) if args.schema else None,
    )
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
