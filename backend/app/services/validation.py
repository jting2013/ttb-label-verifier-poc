import re
from difflib import SequenceMatcher

from app.models.schemas import ExpectedApplication, FieldValidation, FormatObservations, LabelFields, ValidationStatus


GOV_WARNING_EXACT = (
    "GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK "
    "ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. "
    "(2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR "
    "OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS."
)


class ValidationEngine:
    def validate(
        self,
        expected: ExpectedApplication,
        extracted: LabelFields,
        format_observations: FormatObservations | None = None,
    ) -> list[FieldValidation]:
        format_observations = format_observations or FormatObservations()
        return [
            self._brand(expected.fields.brand_name, extracted.brand_name),
            self._fuzzy("class_type", expected.fields.class_type, extracted.class_type, 0.86),
            self._alcohol(expected.fields.alcohol_content, extracted.alcohol_content),
            self._fuzzy("net_contents", expected.fields.net_contents, extracted.net_contents, 0.95),
            self._fuzzy(
                "bottler_producer_name",
                expected.fields.bottler_producer_name,
                extracted.bottler_producer_name,
                0.78,
            ),
            self._fuzzy("country_of_origin", expected.fields.country_of_origin, extracted.country_of_origin, 0.9),
            self._government_warning(
                extracted.government_warning,
                format_observations.government_warning_prefix_bold,
            ),
        ]

    def summarize(self, validations: list[FieldValidation]) -> ValidationStatus:
        if any(item.status == ValidationStatus.FAIL for item in validations):
            return ValidationStatus.FAIL
        if any(item.status == ValidationStatus.WARNING for item in validations):
            return ValidationStatus.WARNING
        return ValidationStatus.PASS

    def _brand(self, expected: str | None, extracted: str | None) -> FieldValidation:
        confidence = _similarity(_soft_normalize(expected), _soft_normalize(extracted))
        status = ValidationStatus.PASS if confidence >= 0.92 else ValidationStatus.FAIL
        return FieldValidation(
            field="brand_name",
            expected=expected,
            extracted=extracted,
            status=status,
            confidence=confidence,
            message="Brand matches expected application data." if status == ValidationStatus.PASS else "Brand name does not match expected application data.",
        )

    def _fuzzy(self, field: str, expected: str | None, extracted: str | None, threshold: float) -> FieldValidation:
        confidence = _similarity(_soft_normalize(expected), _soft_normalize(extracted))
        status = ValidationStatus.PASS if confidence >= threshold else ValidationStatus.WARNING if extracted else ValidationStatus.FAIL
        return FieldValidation(
            field=field,
            expected=expected,
            extracted=extracted,
            status=status,
            confidence=confidence,
            message="Field matches expected value." if status == ValidationStatus.PASS else "Field is missing or differs from expected value.",
        )

    def _alcohol(self, expected: str | None, extracted: str | None) -> FieldValidation:
        expected_abv, expected_proof = _alcohol_numbers(expected)
        extracted_abv, extracted_proof = _alcohol_numbers(extracted)
        ok = bool(expected_abv and extracted_abv and abs(expected_abv - extracted_abv) <= 0.2)
        proof_ok = expected_proof is None or (extracted_proof is not None and abs(expected_proof - extracted_proof) <= 1)
        status = ValidationStatus.PASS if ok and proof_ok else ValidationStatus.FAIL
        confidence = 0.98 if status == ValidationStatus.PASS else 0.35
        return FieldValidation(
            field="alcohol_content",
            expected=expected,
            extracted=extracted,
            status=status,
            confidence=confidence,
            message="ABV/proof values are consistent." if status == ValidationStatus.PASS else "ABV or proof could not be verified.",
        )

    def _government_warning(self, extracted: str | None, prefix_bold: bool | None) -> FieldValidation:
        if not extracted:
            return FieldValidation(
                field="government_warning",
                expected=GOV_WARNING_EXACT,
                extracted=extracted,
                status=ValidationStatus.FAIL,
                confidence=0,
                message="Government warning statement is missing.",
            )
        exact = " ".join(extracted.split()) == GOV_WARNING_EXACT
        upper_prefix = extracted.startswith("GOVERNMENT WARNING:")
        uppercase = extracted == extracted.upper()
        if exact and upper_prefix and uppercase and prefix_bold is True:
            status = ValidationStatus.PASS
            message = "Government warning uses exact required wording; uppercase and bold heading are confirmed."
            confidence = 1.0
        elif exact and upper_prefix and uppercase and prefix_bold is None:
            status = ValidationStatus.WARNING
            message = "Wording and uppercase heading match; confirm that 'GOVERNMENT WARNING:' is bold in the label artwork."
            confidence = 0.8
        elif exact and upper_prefix and uppercase and prefix_bold is False:
            status = ValidationStatus.FAIL
            message = "Required 'GOVERNMENT WARNING:' heading is not bold."
            confidence = 0.35
        elif upper_prefix:
            status = ValidationStatus.WARNING
            message = "Government warning heading is present, but wording or required formatting differs."
            confidence = 0.65
        else:
            status = ValidationStatus.FAIL
            message = "Government warning must begin with exact uppercase 'GOVERNMENT WARNING:' wording."
            confidence = 0.2
        return FieldValidation(
            field="government_warning",
            expected=GOV_WARNING_EXACT,
            extracted=extracted,
            status=status,
            confidence=confidence,
            message=message,
        )


def _soft_normalize(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^A-Z0-9]+", "", value.upper())


def _similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0
    return round(SequenceMatcher(None, left, right).ratio(), 3)


def _alcohol_numbers(value: str | None) -> tuple[float | None, float | None]:
    if not value:
        return None, None
    abv_match = re.search(r"(\d{1,2}(?:\.\d+)?)\s*%?", value)
    proof_match = re.search(r"(\d{2,3})\s*PROOF", value, re.I)
    abv = float(abv_match.group(1)) if abv_match else None
    proof = float(proof_match.group(1)) if proof_match else None
    return abv, proof
