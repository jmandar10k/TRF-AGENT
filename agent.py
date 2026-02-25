import os
import json
import re
import logging
import csv
import io
from groq import Groq
from parser import parse_trf

# Initialize
logger = logging.getLogger(__name__)
client = Groq()

# Constants
DATA_FOLDER = "data"
LLM_MODEL = "llama-3.1-8b-instant"
PROMPT_MAX_LENGTH = 800
TEMPERATURE = 0


# -------------------------------------------------
# OUTPUT FORMATTING
# -------------------------------------------------

def format_as_csv(records):
    """Format records as CSV string"""
    if not records:
        return "No records"
    
    output = io.StringIO()
    fieldnames = ["feature", "status", "value", "remarks", "file"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()


def format_as_json(records):
    """Format records as JSON string"""
    return json.dumps(records, indent=2)


def format_as_markdown(records):
    """Format records as markdown table"""
    if not records:
        return "No records"
    
    lines = ["| Feature | Status | Value | Remarks | File |",
             "|---------|--------|-------|---------|------|"]
    
    for r in records:
        lines.append(f"| {r['feature']} | {r['status']} | {r['value']} | {r['remarks']} | {r['file']} |")
    
    return "\n".join(lines)


def format_selective_columns(records, columns):
    """Format only selected columns"""
    if not records:
        return "No records"
    
    # Valid column names
    valid_cols = {"feature", "status", "value", "remarks", "file"}
    cols_to_show = [c.lower() for c in columns if c.lower() in valid_cols]
    
    if not cols_to_show:
        cols_to_show = ["feature", "status", "value", "file"]
    
    filtered_records = [{col: r.get(col, "") for col in cols_to_show} for r in records]
    return filtered_records


def generate_summary(records):
    """Generate AI summary of records"""
    summary_prompt = f"""Provide a clear, concise summary of these tractor test records. 
Include key findings, patterns, and any issues:

{json.dumps(records, indent=2)}"""

    try:
        final = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": summary_prompt}]
        )
        return final.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return f"Error generating summary: {str(e)}"


def format_count_only(records):
    """Return just the count"""
    return f"Found {len(records)} matching record(s)"


def format_statistics(records):
    """Generate statistics about records"""
    if not records:
        return "No records to analyze"
    
    status_count = {}
    feature_count = {}
    
    for r in records:
        status = r.get("status", "Unknown")
        feature = r.get("feature", "Unknown")
        status_count[status] = status_count.get(status, 0) + 1
        feature_count[feature] = feature_count.get(feature, 0) + 1
    
    stats = f"""
**Statistics for {len(records)} records:**

**By Status:**
"""
    for status, count in status_count.items():
        stats += f"\n- {status}: {count}"
    
    stats += "\n\n**By Feature:**\n"
    for feature, count in feature_count.items():
        stats += f"\n- {feature}: {count}"
    
    return stats

def run_agent(prompt):
    """Run the TRF agent to query and filter test data with flexible output formatting.
    
    Args:
        prompt: User query string (can specify output format)
        
    Returns:
        Formatted results based on user request
    """
    if not prompt or not isinstance(prompt, str):
        return "Error: Invalid prompt"

    prompt = prompt[:PROMPT_MAX_LENGTH]

    # LLM Extraction - extract feature, periods, AND output format preference
    extraction_system = """You are a JSON converter. 

Your job: Convert the user query into JSON object. Return ONLY JSON, nothing else.

Do not write explanation, code blocks, or markdown. Just the JSON object.

Template:
{
  "feature": <feature name or null>,
  "periods": [<list of period objects OR empty list>],
  "format": <output format requested>
}

Period object template:
{"month": <month name or null>, "year": <4-digit year string or null>, "sprint": <sprint number as string or null>}

Format detection rules:
- "summary" if user asks for summary, overview, analysis
- "csv" if user asks for CSV, spreadsheet, export
- "json" if user asks for JSON format
- "markdown" if user asks for markdown, table format
- "count" if user asks for count, total, how many
- "stats" if user asks for stats, statistics, breakdown
- "default" otherwise

Valid output examples:
{"feature": "Braking", "periods": [], "format": "table"}
{"feature": null, "periods": [{"month": "February", "year": "2025", "sprint": "2"}], "format": "csv"}
{"feature": "Steering", "periods": [{"month": "March", "year": "2024", "sprint": "1"}], "format": "summary"}

Remember: Return ONLY the JSON object. No text before or after."""

    try:
        completion = client.chat.completions.create(
            model=LLM_MODEL,
            temperature=TEMPERATURE,
            messages=[
                {"role": "system", "content": extraction_system},
                {"role": "user", "content": prompt}
            ]
        )
        raw = completion.choices[0].message.content.strip()
        # Print raw response for debugging
        print(f"[DEBUG] Raw LLM Response: {repr(raw)}")
        logger.info(f"LLM Response received (length: {len(raw)})")
    except Exception as e:
        logger.error(f"LLM API Error: {e}")
        print(f"[ERROR] LLM API Error: {e}")
        return f"Error querying LLM: {str(e)}"

    # Extract JSON - Try multiple strategies
    json_text = None
    
    # Strategy 1: Remove markdown code blocks if present
    cleaned = re.sub(r"```json\s*", "", raw)
    cleaned = re.sub(r"```\s*", "", cleaned)
    print(f"[DEBUG] After removing code blocks: {repr(cleaned)}")
    
    # Strategy 2: Find the first complete JSON object (greedy for top level)
    matches = list(re.finditer(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", cleaned))
    if matches:
        json_text = matches[0].group()
        print(f"[DEBUG] Found JSON using regex: {repr(json_text)}")
    
    # Strategy 3: If no match, try simple greedy extraction
    if not json_text:
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            json_text = match.group()
            print(f"[DEBUG] Found JSON using greedy search: {repr(json_text)}")
    
    if not json_text:
        logger.error(f"No JSON found in LLM response after strategies: {raw}")
        print(f"[ERROR] Could not extract JSON from: {repr(raw)}")
        return "Failed to extract parameters from query"

    logger.debug(f"Extracted JSON (raw): {json_text}")
    
    # Normalize common LLM JSON mistakes
    json_text = json_text.replace("'", '"')  # Single quotes to double quotes
    json_text = json_text.replace("\\n", " ")  # Remove escaped line breaks
    json_text = json_text.replace("\\t", " ")  # Remove escaped tabs
    json_text = re.sub(r",\s*}", "}", json_text)  # Trailing commas before }
    json_text = re.sub(r",\s*]", "]", json_text)  # Trailing commas before ]
    json_text = re.sub(r":\s*null", ": null", json_text)  # Normalize null spacing
    json_text = re.sub(r'null\s*"', '"', json_text)  # Fix null missing values
    
    # Replace smart quotes with regular quotes
    json_text = json_text.replace(""", '"').replace(""", '"')
    json_text = json_text.replace("'", '"').replace("'", '"')
    
    print(f"[DEBUG] After normalization: {repr(json_text)}")
    
    params = None
    try:
        params = json.loads(json_text)
        print(f"[DEBUG] Successfully parsed JSON: {params}")
        logger.info(f"Parameters parsed: feature={params.get('feature')}, periods count={len(params.get('periods', []))}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed at char {e.pos}: {e.msg}")
        logger.error(f"Context: ...{json_text[max(0, e.pos-20):e.pos+20]}...")
        print(f"[ERROR] JSON parse error at position {e.pos}: {e.msg}")
        print(f"[ERROR] Problematic text: {repr(json_text)}")
        
        # Try one more time with aggressive cleanup
        try:
            cleaned_json = json_text.strip()
            if not cleaned_json.startswith("{"):
                cleaned_json = "{" + cleaned_json
            if not cleaned_json.endswith("}"):
                cleaned_json = cleaned_json + "}"
            params = json.loads(cleaned_json)
            logger.info(f"Successfully parsed after aggressive cleanup")
            print(f"[DEBUG] Success after cleanup: {params}")
        except Exception as e2:
            logger.error(f"Failed all strategies: {e2}")
            print(f"[ERROR] All parsing strategies failed: {e2}")
            return f"Failed to parse query parameters: {json_text[:100]}..."

    # Validate params
    if not isinstance(params, dict):
        logger.error(f"Parameters not a dict: {type(params)}")
        print(f"[ERROR] Parameters is {type(params)}, not dict")
        return "Error: Invalid parameters structure (expected JSON object)"
    
    feature = params.get("feature")
    periods = params.get("periods", [])
    output_format = params.get("format", "default").lower()
    
    if not isinstance(periods, list):
        periods = []
    
    # Validate output format
    valid_formats = {"table", "csv", "json", "markdown", "summary", "count", "stats", "default"}
    if output_format not in valid_formats:
        output_format = "default"
    
    logger.info(f"Agent params: feature={feature}, format={output_format}, periods={len(periods)}")

    # Load all TRF files
    all_rows = []
    
    try:
        if not os.path.exists(DATA_FOLDER):
            logger.error(f"Data folder not found: {DATA_FOLDER}")
            return "Data folder not found"
        
        trf_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".trf")]
        if not trf_files:
            logger.warning("No TRF files found")
            return "No TRF files found in data folder"
        
        for filename in trf_files:
            filepath = os.path.join(DATA_FOLDER, filename)
            rows = parse_trf(filepath)
            for row in rows:
                row["file"] = filename
                all_rows.append(row)
    except Exception as e:
        logger.error(f"Error loading TRF files: {e}")
        return f"Error loading data: {str(e)}"

    if not all_rows:
        logger.warning("No test records found after parsing")
        return "No test records found"

    # Filter results (avoid duplicates with set)
    result_ids = set()
    results = []

    for row in all_rows:
        # Feature filter
        if feature and feature.lower() not in row["feature"].lower():
            continue

        # Period filter (OR logic): if no periods, include all; if periods exist, match any
        include_row = not periods  # If no periods specified, include
        
        if periods:
            for period in periods:
                match_period = True
                
                # Check month (3-letter abbreviation)
                if period.get("month"):
                    month_abbr = period["month"][:3].lower()
                    if month_abbr not in row["file"].lower():
                        match_period = False
                
                # Check year
                if period.get("year") and match_period:
                    if str(period["year"]) not in row["file"]:
                        match_period = False
                
                # Check sprint
                if period.get("sprint") and match_period:
                    if str(period["sprint"]) not in row["file"]:
                        match_period = False
                
                if match_period:
                    include_row = True
                    break
        
        if include_row:
            # Use tuple to create unique key per row (avoid duplicates)
            row_key = (row["feature"], row["status"], row["value"], row["file"])
            if row_key not in result_ids:
                result_ids.add(row_key)
                results.append(row)

    if not results:
        logger.info("No matching records found")
        return "No matching records found"

    # Format results based on user request
    logger.info(f"Formatting {len(results)} results as: {output_format}")
    
    if output_format == "csv":
        return format_as_csv(results)
    elif output_format == "json":
        return format_as_json(results)
    elif output_format == "markdown":
        return format_as_markdown(results)
    elif output_format == "count":
        return format_count_only(results)
    elif output_format == "stats":
        return format_statistics(results)
    elif output_format == "summary":
        return generate_summary(results)
    else:  # default or "table"
        return results
