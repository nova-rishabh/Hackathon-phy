"""Export JSON Schemas from contracts/models.py.

    python -m contracts.export

Writes contracts/schemas/<Model>.schema.json and contracts/schemas/all.schema.json.
Web types (run by B1 once web/ exists):
    pnpm dlx json-schema-to-typescript -i contracts/schemas/all.schema.json -o web/lib/types.ts
"""
import json
from pathlib import Path

from pydantic.json_schema import models_json_schema

from contracts.models import EXPORTED

OUT = Path(__file__).parent / "schemas"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for model in EXPORTED:
        path = OUT / f"{model.__name__}.schema.json"
        path.write_text(json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2), encoding="utf-8")

    _, combined = models_json_schema([(m, "validation") for m in EXPORTED], title="RollWatch")
    # json-schema-to-typescript only emits types reachable from the root, so reference every model.
    combined["type"] = "object"
    combined["properties"] = {m.__name__: {"$ref": f"#/$defs/{m.__name__}"} for m in EXPORTED}
    (OUT / "all.schema.json").write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(EXPORTED)} schemas + all.schema.json to {OUT}")


if __name__ == "__main__":
    main()
