import re

from app.models.schemas import LabelFields


ABV_RE = re.compile(r"(?P<abv>\d{1,2}(?:\.\d+)?)\s*%?\s*(?:ALC\.?/VOL\.?|ABV)", re.I)
PROOF_RE = re.compile(r"(?P<proof>\d{2,3})\s*PROOF", re.I)
NET_RE = re.compile(r"(?P<net>\d+(?:\.\d+)?)\s*(?:ML|L|LITER|LITRE|OZ)", re.I)
WARNING_RE = re.compile(
    r"GOVERNMENT\s+WARNING\s*:.*?MAY\s+CAUSE\s+HEALTH\s+PROBLEMS\.",
    re.I | re.S,
)
COUNTRY_RE = re.compile(r"(?:PRODUCT OF|COUNTRY OF ORIGIN|ORIGIN)\s*:?\s*([^\n]+)", re.I)
PRODUCER_RE = re.compile(r"(?:BOTTLED BY|PRODUCED BY|DISTILLED BY|BREWED BY)\s+(.+)", re.I)
TYPE_HINTS = (
    "WHISKEY",
    "WHISKY",
    "BOURBON",
    "VODKA",
    "GIN",
    "RUM",
    "TEQUILA",
    "WINE",
    "BEER",
    "LAGER",
    "ALE",
    "BRANDY",
)


def normalize_lines(text: str) -> list[str]:
    return [line.strip(" -\t") for line in text.splitlines() if line.strip()]


def parse_label_fields(text: str) -> LabelFields:
    source_lines = normalize_lines(text)
    source_text = "\n".join(source_lines)
    lines = [line.upper() for line in source_lines]
    full_text = "\n".join(lines)

    abv = ABV_RE.search(full_text)
    proof = PROOF_RE.search(full_text)
    alcohol_content = None
    if abv and proof:
        alcohol_content = f"{abv.group('abv')}% Alc./Vol. ({proof.group('proof')} Proof)"
    elif abv:
        alcohol_content = f"{abv.group('abv')}% Alc./Vol."
    elif proof:
        alcohol_content = f"{proof.group('proof')} Proof"

    net = NET_RE.search(full_text)
    warning = WARNING_RE.search(source_text)
    country = COUNTRY_RE.search(full_text)
    producer = PRODUCER_RE.search(full_text)

    class_type = next(
        (line.title() for line in lines if any(hint in line for hint in TYPE_HINTS)),
        None,
    )
    brand_name = _candidate_brand(lines, class_type)

    return LabelFields(
        brand_name=brand_name,
        class_type=class_type,
        alcohol_content=alcohol_content,
        net_contents=net.group(0).replace("ML", "mL") if net else None,
        bottler_producer_name=producer.group(1).title() if producer else None,
        country_of_origin=country.group(1).strip().title() if country else None,
        government_warning=warning.group(0).strip() if warning else None,
    )


def _candidate_brand(lines: list[str], class_type: str | None) -> str | None:
    skip_terms = {"GOVERNMENT", "WARNING", "ALC", "PROOF", "BOTTLED", "PRODUCED", "DISTILLED"}
    for line in lines[:6]:
        if class_type and line.title() == class_type:
            continue
        if any(term in line for term in skip_terms):
            continue
        if len(line) >= 4:
            return line.title()
    return None
