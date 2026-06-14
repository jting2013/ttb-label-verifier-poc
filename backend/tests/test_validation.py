from app.models.schemas import ExpectedApplication, FormatObservations, LabelFields
from app.services.parser import parse_label_fields
from app.services.validation import GOV_WARNING_EXACT, ValidationEngine, ValidationStatus


def _expected() -> ExpectedApplication:
    return ExpectedApplication(
        application_id="APP-1",
        label_name="Test",
        fields=LabelFields(
            brand_name="STONE'S THROW",
            class_type="Kentucky Straight Bourbon Whiskey",
            alcohol_content="45% Alc./Vol. (90 Proof)",
            net_contents="750 mL",
            bottler_producer_name="Old Tom Distillery Co., Louisville, KY",
            country_of_origin="United States",
            government_warning=GOV_WARNING_EXACT,
        ),
    )


def test_brand_matching_tolerates_case_and_punctuation() -> None:
    result = ValidationEngine().validate(_expected(), LabelFields(brand_name="Stone's Throw"))
    brand = next(item for item in result if item.field == "brand_name")
    assert brand.status == ValidationStatus.PASS


def test_government_warning_requires_uppercase_prefix() -> None:
    result = ValidationEngine().validate(_expected(), LabelFields(government_warning="Government warning: pregnancy risk"))
    warning = next(item for item in result if item.field == "government_warning")
    assert warning.status == ValidationStatus.FAIL


def test_government_warning_rejects_title_case_even_with_exact_words() -> None:
    title_case_heading = GOV_WARNING_EXACT.replace("GOVERNMENT WARNING:", "Government Warning:")
    result = ValidationEngine().validate(
        _expected(),
        parse_label_fields(title_case_heading),
        FormatObservations(government_warning_prefix_bold=True, source="fixture"),
    )
    warning = next(item for item in result if item.field == "government_warning")
    assert warning.status == ValidationStatus.FAIL


def test_government_warning_passes_when_exact_text_and_bold_prefix_are_verified() -> None:
    result = ValidationEngine().validate(
        _expected(),
        LabelFields(government_warning=GOV_WARNING_EXACT),
        FormatObservations(government_warning_prefix_bold=True, source="fixture"),
    )
    warning = next(item for item in result if item.field == "government_warning")
    assert warning.status == ValidationStatus.PASS


def test_government_warning_requires_visual_review_when_bold_is_unverified() -> None:
    result = ValidationEngine().validate(_expected(), LabelFields(government_warning=GOV_WARNING_EXACT))
    warning = next(item for item in result if item.field == "government_warning")
    assert warning.status == ValidationStatus.WARNING


def test_alcohol_content_accepts_abv_and_proof() -> None:
    result = ValidationEngine().validate(_expected(), LabelFields(alcohol_content="45% ABV 90 proof"))
    alcohol = next(item for item in result if item.field == "alcohol_content")
    assert alcohol.status == ValidationStatus.PASS
