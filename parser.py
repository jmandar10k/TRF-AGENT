import re
import logging

logger = logging.getLogger(__name__)

def parse_trf(file_path):
    """Parse a TRF file and extract feature test data.
    
    Args:
        file_path: Path to the .trf file
        
    Returns:
        List of feature dictionaries, or empty list on error
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []

    if not content.strip():
        logger.warning(f"Empty file: {file_path}")
        return []

    blocks = content.split("---")
    features = []
    pattern = r"([A-Za-z_]+)\s*=\s*(.+)"

    for block in blocks:
        if not block.strip():
            continue
            
        try:
            data = {}
            for match in re.finditer(pattern, block):
                key = match.group(1).lower()
                value = match.group(2).strip()
                data[key] = value
            
            if "feature_name" in data:
                features.append({
                    "feature": data.get("feature_name", ""),
                    "status": data.get("status", ""),
                    "value": data.get("measured_value", ""),
                    "remarks": data.get("remarks", "")
                })
        except Exception as e:
            logger.warning(f"Error parsing block in {file_path}: {e}")
            continue

    return features
