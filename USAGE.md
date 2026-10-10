# Find Duplicates — Usage Manual

A Python tool that identifies potential duplicate contacts in a CSV file using weighted field matching.

## Requirements

- Python 3.8+

## Installation

No dependencies beyond the standard library. Clone or copy `find_duplicates.py` to your project.

## Usage

```bash
python3 find_duplicates.py --input <input.csv> --output <output.csv>
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--input`  | Yes | Path to input CSV with contact data |
| `--output` | Yes | Path where result CSV will be written |

### Input format

The input CSV must have these exact column headers:

```
contactID,name,name1,email,postalZip,address
```

| Column | Description |
|--------|-------------|
| `contactID` | Unique identifier for each contact |
| `name` | First name (may be full name or initial) |
| `name1` | Last name (may be full name or initial) |
| `email` | Email address (may be empty) |
| `postalZip` | ZIP/postal code (may be empty) |
| `address` | Street address (may be empty) |

Any fields can be empty — the tool handles missing data gracefully.

### Output format

```
contactID_source,contactID_match,accuracy
```

| Column | Description |
|--------|-------------|
| `contactID_source` | The contact with the lower ID (always source < match) |
| `contactID_match` | The contact with the higher ID |
| `accuracy` | Match confidence: `High`, `Medium`, or `Low` |

Only pairs scoring ≥20 are included. Scores below 20 are discarded as noise.

## Matching logic

### Score components

| Condition | Points |
|-----------|--------|
| Email exact match | 40 |
| Email same local part, different domain | 35 |
| Last name exact match | 20 |
| ZIP code exact match | 15 |
| First name exact match | 15 |
| First name is initial of the other (e.g. "C" ≈ "Ciara") | 12 |
| First names share first letter | 5 |
| Address has 2+ normalized tokens in common | 10 |
| Address has 1 normalized token in common | 5 |

Max possible score per pair: **100**.

### Accuracy thresholds

| Score range | Label |
|-------------|-------|
| ≥ 70 | High |
| 40–69 | Medium |
| 20–39 | Low |
| < 20 | (excluded) |

### Address normalization

Before comparison, addresses are cleaned:
1. Common prefixes (`P.O. Box`, `Ap #`, `No.`) and their following numbers are removed
2. Punctuation is stripped
3. Text is lowercased
4. Remaining tokens are compared as sets

## Examples

### Basic usage

```bash
python3 find_duplicates.py --input contacts.csv --output results.csv
```

### Sample input

```csv
contactID,name,name1,email,postalZip,address
1,Ciara,French,mollis.lectus.pede@outlook.net,39746,449-6990 Tellus. Rd.
2,C,French,mollis.lectus.pede@yahoo.net,39746,449-6990 Tellus. Rd.
```

### Sample output

```csv
contactID_source,contactID_match,accuracy
1,2,High
```

### Run tests

```bash
python3 -m pytest test_find_duplicates.py -v
```

## Performance

Scales as O(n²/2) — a 1000-contact file (~500k pair comparisons) completes in under a second.

## Test file

`test_find_duplicates.py` contains 39 tests covering:
- Field normalization (email, name, address)
- Each scoring component independently
- Score integration for match / no-match pairs
- Classification thresholds and boundaries
- Full end-to-end pipeline with known duplicate data