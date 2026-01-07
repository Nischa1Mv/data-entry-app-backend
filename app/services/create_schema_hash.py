import hashlib
import re
from typing import Dict, Any, List, Tuple

LAYOUT_FIELD_TYPES = {
    "Section Break",
    "Column Break",
    "HTML"
}

def normalize_fieldname(name: str, all_names: List[str]) -> str:
    """
    Remove trailing digits ONLY if base name is unique.
    """
    base = re.sub(r"\d+$", "", name)
    if base != name and all_names.count(base) == 1:
        return base
    return name


def normalize_options(fieldtype: str, options: Any) -> str:
    """
    Normalize options safely across field types.
    """
    if options is None:
        return ""

    options = str(options).strip()

    # Normalize Select options (newline separated)
    if fieldtype == "Select":
        return "\n".join(
            line.strip() for line in options.splitlines() if line.strip()
        )

    return options


def create_schema_hash(doctype_schema: Dict[str, Any]) -> str:
    fields = doctype_schema.get("fields", [])

    # Collect all fieldnames first
    all_names = [f.get("fieldname", "") for f in fields]

    simplified_fields = []

    for field in fields:
        fieldtype = field.get("fieldtype", "")
        fieldname = field.get("fieldname", "")

        # Skip layout-only fields
        if fieldtype in LAYOUT_FIELD_TYPES:
            continue

        normalized_name = normalize_fieldname(fieldname, all_names)
        normalized_options = normalize_options(
            fieldtype, field.get("options", "")
        )

        simplified_fields.append({
            "fieldname": normalized_name,
            "fieldtype": fieldtype,
            "options": normalized_options
        })

    # Deterministic ordering
    simplified_fields.sort(
        key=lambda f: (f["fieldname"], f["fieldtype"], f["options"])
    )

    concat_str = "|".join(
        f"{f['fieldname']}:{f['fieldtype']}:{f['options']}"
        for f in simplified_fields
    )

    schema_hash = hashlib.sha256(
        concat_str.encode("utf-8")
    ).hexdigest()

    return schema_hash
