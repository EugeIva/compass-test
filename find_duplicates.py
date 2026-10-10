import csv
import re
import argparse
from collections.abc import Iterator


NORMALIZE_ADDRESS_PREFIXES = re.compile(
    r'\b(p\.?\s*o\.?\s*box|ap(?:t)?\.?\s*#?|no\.?)\s*\d+\b',
    re.IGNORECASE,
)
NORMALIZE_PUNCTUATION = re.compile(r'[^\w\s]+')
NORMALIZE_WHITESPACE = re.compile(r'\s+')


def normalize_string(s: str) -> str:
    return NORMALIZE_WHITESPACE.sub(' ', NORMALIZE_PUNCTUATION.sub(' ', s.lower())).strip()


def email_local_part(email: str) -> str:
    return email.split('@')[0].strip().lower() if email and '@' in email else ''


def email_domain(email: str) -> str:
    parts = email.split('@')
    return parts[1].strip().lower() if len(parts) == 2 else ''


def name_is_initial(name: str) -> bool:
    return len(name.strip()) == 1


def names_match(first_a: str, last_a: str, first_b: str, last_b: str) -> tuple[int, int]:
    first_score = 0
    last_score = 0

    if last_a and last_b and last_a == last_b:
        last_score = 20

    if first_a and first_b:
        if first_a == first_b:
            first_score = 15
        elif name_is_initial(first_a) and not name_is_initial(first_b) and first_b.startswith(first_a):
            first_score = 12
        elif name_is_initial(first_b) and not name_is_initial(first_a) and first_a.startswith(first_b):
            first_score = 12
        elif first_a[0] == first_b[0]:
            first_score = 5

    return first_score, last_score


def emails_match(email_a: str, email_b: str) -> int:
    if not email_a or not email_b:
        return 0
    local_a, local_b = email_local_part(email_a), email_local_part(email_b)
    domain_a, domain_b = email_domain(email_a), email_domain(email_b)
    if not local_a or not local_b:
        return 0
    if local_a == local_b:
        if domain_a == domain_b:
            return 40
        return 35
    return 0


def zips_match(zip_a: str, zip_b: str) -> int:
    return 15 if zip_a and zip_b and zip_a == zip_b else 0


def addresses_match(addr_a: str, addr_b: str) -> int:
    def normalize_addr(a: str) -> set[str]:
        cleaned = NORMALIZE_ADDRESS_PREFIXES.sub('', a)
        tokens = set(NORMALIZE_WHITESPACE.sub(' ', NORMALIZE_PUNCTUATION.sub(' ', cleaned.lower())).split())
        tokens.discard('')
        return tokens

    if not addr_a or not addr_b:
        return 0
    tokens_a, tokens_b = normalize_addr(addr_a), normalize_addr(addr_b)
    if not tokens_a or not tokens_b:
        return 0
    intersection = tokens_a & tokens_b
    if len(intersection) >= 2:
        return 10
    if len(intersection) == 1:
        return 5
    return 0


def score_pair(row_a: dict, row_b: dict) -> int:
    first_score, last_score = names_match(
        row_a['name'].strip().lower(),
        row_a['name1'].strip().lower(),
        row_b['name'].strip().lower(),
        row_b['name1'].strip().lower(),
    )
    email_score = emails_match(
        row_a['email'].strip().lower(),
        row_b['email'].strip().lower(),
    )
    zip_score = zips_match(
        row_a['postalZip'].strip(),
        row_b['postalZip'].strip(),
    )
    addr_score = addresses_match(
        row_a['address'].strip(),
        row_b['address'].strip(),
    )
    return first_score + last_score + email_score + zip_score + addr_score


def classify(score: int) -> str:
    if score >= 70:
        return 'High'
    if score >= 40:
        return 'Medium'
    if score >= 20:
        return 'Low'
    return None


def load_csv(path: str) -> list[dict]:
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def find_duplicates(rows: list[dict]) -> Iterator[dict]:
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            score = score_pair(rows[i], rows[j])
            accuracy = classify(score)
            if accuracy:
                yield {
                    'contactID_source': rows[i]['contactID'],
                    'contactID_match': rows[j]['contactID'],
                    'accuracy': accuracy,
                }


def write_output(rows: Iterator[dict], path: str):
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['contactID_source', 'contactID_match', 'accuracy'])
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description='Identify duplicate contacts in a CSV file.')
    parser.add_argument('--input', required=True, help='Path to input CSV')
    parser.add_argument('--output', required=True, help='Path to output CSV')
    args = parser.parse_args()
    rows = load_csv(args.input)
    duplicates = find_duplicates(rows)
    write_output(duplicates, args.output)
    print(f'Results written to {args.output}')


if __name__ == '__main__':
    main()