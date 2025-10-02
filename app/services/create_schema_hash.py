import hashlib
from typing import Dict, Any

def create_schema_hash(doctype_schema: Dict[str, Any]) -> str:
    fields = doctype_schema.get('fields', [])
    
    # Create simplified field representations
    simplified_fields = []
    for field in fields:
        simplified_field = {
            'fieldname': field.get('fieldname', ''),
            'fieldtype': field.get('fieldtype', ''),
            'options': field.get('options', '')
        }
        simplified_fields.append(simplified_field)
    
    simplified_fields.sort(key=lambda x: x['fieldname'])
    
    concat_str = '|'.join(
        f"{field['fieldname']}:{field['fieldtype']}:{field['options']}"
        for field in simplified_fields
    )
    
    return hashlib.sha256(concat_str.encode('utf-8')).hexdigest()
