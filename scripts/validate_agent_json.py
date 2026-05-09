"""Validate agent JSON output and write a repair-only prompt on failure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


def _write_repair_prompt(output_path: Path, input_path: Path, schema_path: Path, error_kind: str, error_message: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prompt = f"""# Agent JSON Repair Prompt

The file below failed validation:

`{input_path}`

Schema:

`{schema_path}`

Failure type:

{error_kind}

Error:

```text
{error_message}
```

请只修复 JSON 语法或 schema 问题，不要改写实质内容，不要删减已有字段，不要新增未要求的事实。

修复规则：

1. 输出必须是严格 JSON，不要 Markdown 代码块。
2. 如果字符串中包含引号，请改用中文引号或正确转义。
3. 如果 schema 要求数组，不要写 `null`，空值写 `[]`。
4. 如果 schema 要求对象，不要写字符串或数组。
5. 保留原计划中的 problem_diagnosis、evidence_coverage、actions、synchronized_updates、author_input_needed、risks。
6. 修复后覆盖原文件或写入指定 retry 文件，并再次运行 validate。
"""
    output_path.write_text(prompt, encoding="utf-8")


def validate_agent_json(schema_path: Path, input_path: Path, repair_prompt: Path | None = None) -> tuple[bool, str]:
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        message = f"{exc.msg} at line {exc.lineno} column {exc.colno} (char {exc.pos})"
        if repair_prompt:
            _write_repair_prompt(repair_prompt, input_path, schema_path, "JSON syntax error", message)
        return False, f"JSON syntax error: {message}"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda err: list(err.path))
    if errors:
        first: ValidationError = errors[0]
        path = "$" + "".join(f"[{part!r}]" if isinstance(part, int) else f".{part}" for part in first.path)
        message = f"{path}: {first.message}"
        if repair_prompt:
            _write_repair_prompt(repair_prompt, input_path, schema_path, "Schema validation error", message)
        return False, f"Schema validation error: {message}"
    return True, "valid"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate agent JSON and generate repair prompt on failure.")
    parser.add_argument("--schema", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--repair-prompt")
    args = parser.parse_args()
    ok, message = validate_agent_json(
        Path(args.schema),
        Path(args.input),
        Path(args.repair_prompt) if args.repair_prompt else None,
    )
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
