from collections import defaultdict
from collections.abc import Mapping, Sequence


def format_value(format_str: str, value):
    if isinstance(value, Mapping):
        return format_str.format(**value)
    if isinstance(value, Sequence) and not isinstance(value, str):
        return [
            format_str.format_map(defaultdict(str, v)) if isinstance(v, Mapping) else format_str.format(v) 
            for v in value
        ]
    
    return format_str.format(value)

def map_source_record(source_record: dict, mapping: dict) -> dict:
    formatted_record = {}
    
    for key, entries in mapping.items():
        if isinstance(entries, tuple):
            record_key, format_str = entries
            value = source_record.get(record_key)
            
            if value is not None:
                formatted_record[key] = format_value(format_str, value)
        elif isinstance(entries, list):
            mapped_values = []
            
            for entry in entries:
                record_key, format_str = entry
                value = source_record.get(record_key)
                
                if value is not None:
                    formatted_value = format_value(format_str, value)
                    
                    if isinstance(formatted_value, list):
                        mapped_values.extend(formatted_value)
                    else:
                        mapped_values.append(formatted_value)
            
            if mapped_values:
                formatted_record[key] = mapped_values
    
    return formatted_record
