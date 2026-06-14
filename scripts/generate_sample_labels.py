"""Generate controlled label artwork for the TTB verification prototype.

Run without arguments to regenerate the three canonical fixtures. Use
``--count`` to create an additional batch under ``sample_data/generated_labels``.
All outputs are registered by SHA-256 checksum for deterministic demo review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
LABEL_DIR = ROOT / "sample_data" / "labels"
GENERATED_DIR = ROOT / "sample_data" / "generated_labels"
MANIFEST_PATH = ROOT / "sample_data" / "expected" / "controlled_fixtures.json"
GENERATED_REPORT_PATH = ROOT / "sample_data" / "expected" / "generated_outputs.json"

WARNING_LINES = [
    "GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK",
    "ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS.",
    "(2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR",
    "OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS.",
]
VALID_LINES = [
    "OLD TOM DISTILLERY",
    "Kentucky Straight Bourbon Whiskey",
    "45% Alc./Vol. (90 Proof)",
    "750 mL",
    "Bottled by Old Tom Distillery Co., Louisville, KY",
    "Country of Origin: United States",
    *WARNING_LINES,
]
INVALID_WARNING_LINES = [
    *VALID_LINES[:6],
    "Government warning: pregnancy risk. Do not drink and drive.",
]


@dataclass(frozen=True)
class FixtureSpec:
    filename: str
    lines: list[str]
    expected_status: str
    notes: str
    warning_prefix_bold: bool | None
    rotate: float = 0
    blur: float = 0
    glare: bool = False


def canonical_specs() -> list[FixtureSpec]:
    return [
        FixtureSpec(
            "valid_old_tom.png",
            VALID_LINES,
            "PASS",
            "Baseline compliant label with exact bold warning heading.",
            True,
        ),
        FixtureSpec(
            "invalid_warning.png",
            INVALID_WARNING_LINES,
            "FAIL",
            "Incomplete warning text with noncompliant heading casing.",
            False,
        ),
        FixtureSpec(
            "rotated_blurry.png",
            VALID_LINES,
            "PASS",
            "Compliant fixture photographed with rotation and blur.",
            True,
            rotate=-7,
            blur=1.2,
        ),
    ]


def batch_specs(count: int) -> list[FixtureSpec]:
    templates = [
        FixtureSpec("valid_clean", VALID_LINES, "PASS", "Compliant clean artwork.", True),
        FixtureSpec("valid_rotated", VALID_LINES, "PASS", "Compliant rotated artwork.", True, rotate=-5),
        FixtureSpec("valid_soft_blur", VALID_LINES, "PASS", "Compliant softly blurred artwork.", True, blur=0.65),
        FixtureSpec("valid_glare", VALID_LINES, "PASS", "Compliant artwork with simulated glare.", True, glare=True),
        FixtureSpec("valid_angle_glare", VALID_LINES, "PASS", "Compliant artwork with rotation and glare.", True, rotate=4, glare=True),
        FixtureSpec(
            "fail_warning_case",
            [*VALID_LINES[:6], WARNING_LINES[0].replace("GOVERNMENT WARNING:", "Government Warning:"), *WARNING_LINES[1:]],
            "FAIL",
            "Exact warning wording with noncompliant title-case heading.",
            False,
        ),
        FixtureSpec("fail_warning_missing", VALID_LINES[:6], "FAIL", "Mandatory government warning omitted.", None),
        FixtureSpec(
            "fail_abv",
            [VALID_LINES[0], VALID_LINES[1], "40% Alc./Vol. (80 Proof)", *VALID_LINES[3:]],
            "FAIL",
            "Alcohol content differs from the expected application.",
            True,
        ),
        FixtureSpec(
            "fail_net_contents",
            [*VALID_LINES[:3], "700 mL", *VALID_LINES[4:]],
            "WARNING",
            "Net contents differ from the expected application.",
            True,
        ),
        FixtureSpec(
            "fail_brand",
            ["RIVER BEND DISTILLING", *VALID_LINES[1:]],
            "FAIL",
            "Brand name differs from the expected application.",
            True,
        ),
    ]
    generated: list[FixtureSpec] = []
    for index in range(count):
        template = templates[index % len(templates)]
        cycle = index // len(templates) + 1
        suffix = f"_set{cycle}" if cycle > 1 else ""
        generated.append(
            FixtureSpec(
                filename=f"sample_{index + 1:02d}_{template.filename}{suffix}.png",
                lines=template.lines,
                expected_status=template.expected_status,
                notes=template.notes,
                warning_prefix_bold=template.warning_prefix_bold,
                rotate=template.rotate,
                blur=template.blur,
                glare=template.glare,
            )
        )
    return generated


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def draw_label(spec: FixtureSpec, output_path: Path) -> None:
    image = Image.new("RGB", (1200, 760), "#f8f7f0")
    draw = ImageDraw.Draw(image)
    draw.rectangle((36, 36, 1164, 724), outline="#2b2b2b", width=5)
    draw.rectangle((70, 70, 1130, 690), outline="#9f7b3f", width=3)
    y = 100
    for index, line in enumerate(spec.lines):
        size = 54 if index == 0 else 36 if index == 1 else 25
        selected_font = font(size)
        bbox = draw.textbbox((0, 0), line, font=selected_font)
        x = (1200 - (bbox[2] - bbox[0])) // 2 if index < 4 else 95
        if line.startswith("GOVERNMENT WARNING:"):
            prefix = "GOVERNMENT WARNING:"
            prefix_font = font(size, bold=True)
            draw.text((x, y), prefix, fill="#1f2933", font=prefix_font)
            prefix_width = draw.textbbox((0, 0), prefix, font=prefix_font)[2]
            draw.text((x + prefix_width + 5, y), line[len(prefix):].lstrip(), fill="#1f2933", font=selected_font)
        else:
            draw.text((x, y), line, fill="#1f2933", font=selected_font)
        y += 72 if index == 0 else 54 if index == 1 else 39
    if spec.glare:
        glare = Image.new("RGBA", image.size, (0, 0, 0, 0))
        glare_draw = ImageDraw.Draw(glare)
        glare_draw.ellipse((720, 60, 1110, 430), fill=(255, 255, 255, 68))
        glare_draw.ellipse((785, 95, 1040, 360), fill=(255, 255, 255, 48))
        image = Image.alpha_composite(image.convert("RGBA"), glare).convert("RGB")
    if spec.rotate:
        image = image.rotate(spec.rotate, expand=True, fillcolor="#f8f7f0")
    if spec.blur:
        image = image.filter(ImageFilter.GaussianBlur(spec.blur))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def fixture_record(spec: FixtureSpec, path: Path, source: str) -> dict:
    return {
        "filename": spec.filename,
        "relative_path": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
        "expected_status": spec.expected_status,
        "notes": spec.notes,
        "ocr_text": "\n".join(spec.lines),
        "government_warning_prefix_bold": spec.warning_prefix_bold,
        "source": source,
    }


def generate(count: int, output_dir: Path, clean: bool) -> None:
    LABEL_DIR.mkdir(parents=True, exist_ok=True)
    if clean and output_dir.exists():
        for file in output_dir.glob("*.png"):
            file.unlink()

    records: list[dict] = []
    for spec in canonical_specs():
        path = LABEL_DIR / spec.filename
        draw_label(spec, path)
        records.append(fixture_record(spec, path, "canonical"))

    generated_specs = batch_specs(count)
    for spec in generated_specs:
        path = output_dir / spec.filename
        draw_label(spec, path)
        records.append(fixture_record(spec, path, "generated"))

    MANIFEST_PATH.write_text(json.dumps({"fixtures": records}, indent=2) + "\n", encoding="utf-8")
    generated_report = {
        "count": len(generated_specs),
        "output_directory": str(output_dir.relative_to(ROOT)),
        "samples": [
            {key: value for key, value in record.items() if key not in {"ocr_text", "sha256"}}
            for record in records
            if record["source"] == "generated"
        ],
    }
    GENERATED_REPORT_PATH.write_text(json.dumps(generated_report, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(generated_specs)} batch sample image(s) in {output_dir}")
    print(f"Registered {len(records)} controlled fixture(s) in {MANIFEST_PATH}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate controlled alcohol label sample images.")
    parser.add_argument("--count", type=int, default=0, help="Number of additional batch samples to generate.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=GENERATED_DIR,
        help="Output directory for additional batch samples.",
    )
    parser.add_argument("--clean", action="store_true", help="Remove existing PNGs from the batch output directory first.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.count < 0:
        raise SystemExit("--count must be zero or greater")
    target = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    generate(args.count, target, args.clean)
