# TRF-AGENT

# 🚜 TRF Agent - Flexible Test Report Analyzer

A Groq-powered AI agent that intelligently parses and filters tractor test reports (TRF) with flexible output formatting.

## Features

✅ **Natural Language Queries** - Ask in plain English, the AI understands context
✅ **Flexible Output Formats** - Get results in any format you need
✅ **Smart Filtering** - Filter by features, months, years, and sprints
✅ **AI Summaries** - Generate intelligent summaries of test data
✅ **Error Handling** - Robust error handling and logging throughout
✅ **Download Options** - Export results as CSV, JSON, or text

## Installation

```bash
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install groq streamlit

# Set up API key
# Export GROQ_API_KEY=your_api_key_here
```

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

## Query Examples

### Table Format (Default)
```
"Get braking test results from February 2025"
"Show steering data from Sprint 2"
```
**Returns:** Interactive table with all matching records

### CSV Format
```
"Get braking test data from February 2025 sprint 2 as CSV"
"Export steering test results as CSV"
```
**Returns:** CSV-formatted data ready to download

### JSON Format
```
"Get all engine test data as JSON"
"Return braking tests in JSON format"
```
**Returns:** Valid JSON string output

### Markdown Format
```
"Show transmission tests as markdown table"
"Give me hydraulics data as markdown"
```
**Returns:** Markdown-formatted table

### Summary
```
"Give me a summary of steering tests"
"Summarize all test results"
"What's the overview of February 2025 tests?"
```
**Returns:** AI-generated comprehensive summary

### Statistics
```
"Show statistics for all tests"
"Give me stats on March 2024 sprint tests"
"Break down test results by status"
```
**Returns:** Formatted statistics with counts and percentages

### Count Only
```
"How many tests are there from February 2025?"
"Count the passing tests in sprint 2"
"How many braking tests passed?"
```
**Returns:** Simple count of matching records

## Supported Features
- ✅ Steering
- ✅ Braking
- ✅ Suspension
- ✅ Transmission
- ✅ Engine
- ✅ Hydraulics
- ✅ Lights

## Data Format

TRF files follow this format:
```
Test Month: February 2024
Sprint: 2

Feature_Name = Steering
Status = PASS
Measured_Value = 0.88
Remarks = OK

---

Feature_Name = Braking
Status = FAIL
Measured_Value = 0.65
Remarks = Alignment issue
```

## Output Formats

| Format | Usage | Example |
|--------|-------|---------|
| **table** | Interactive data view | Default display |
| **csv** | Spreadsheet export | "...as CSV" |
| **json** | API-ready format | "...as JSON" |
| **markdown** | Document format | "...as markdown" |
| **summary** | AI analysis | "summarize..." |
| **stats** | Statistics breakdown | "statistics..." |
| **count** | Record count | "how many..." |

## Flexible Query Structure

The agent intelligently parses queries with:
- **Feature filters**: steering, braking, suspension, etc.
- **Time periods**: months, years, sprints
- **Output format**: CSV, JSON, summary, stats, count, markdown, table

Mix and match in any order!

## Architecture

- **agent.py**: Main agent logic with LLM extraction and filtering
- **parser.py**: TRF file parsing with error handling
- **app.py**: Streamlit UI with flexible output handling
- **data/**: TRF test files

## Error Handling

- JSON parsing with multiple recovery strategies
- File I/O error handling and validation
- LLM API error handling
- Graceful fallbacks for malformed data

## Logging

Debug mode shows:
- Raw LLM responses
- JSON extraction steps
- Parsing progress
- Filter results

Check console output for detailed `[DEBUG]` messages.

## Future Enhancements

- Database integration for larger datasets
- Custom field selection
- Advanced time range filtering
- Report scheduling
- Multi-user collaboration

---

**Built with Groq AI • Powered by Streamlit**
