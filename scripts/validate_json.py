"""Validate a JSON file against a JSON Schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def validate(schema_path: Path, input_path: Path) -> tuple[bool, str]:
    from jsonschema import Draft202012Validator

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    data = json.loads(input_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda error: list(error.path))
    if not errors:
        return True, "valid"
    first = errors[0]
    path = "$" + "".join(f"[{part!r}]" if isinstance(part, int) else f".{part}" for part in first.path)
    return False, f"{path}: {first.message}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate JSON with schema.")
    parser.add_argument("--schema", required=True)
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    ok, message = validate(Path(args.schema), Path(args.input))
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

