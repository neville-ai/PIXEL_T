"""Unit tests for ColonoscopyDomainValidator.

Tests validation behavior across:
- Colonoscopy with polyp (ACCEPT)
- Normal colonoscopy without polyp (ACCEPT)
- Colonoscopy with dark circular aperture/vignetting (ACCEPT)
- Human face portrait (REJECT)
- Food (pizza, salad, meal) (REJECT)
- Landscape (sky, grass, mountains) (REJECT)
- Document / text screenshot (REJECT)
- Vehicle / car (REJECT)
- Medical non-colonoscopy (grayscale X-ray / MRI) (UNCERTAIN — Kandidat 2: G4 grayscale → UNCERTAIN)
- Animal image (REJECT)
- Severely underexposed / dark ambiguous image (UNCERTAIN)
- Invalid / corrupted / extreme dimensions (REJECT)
- Pure grayscale image (UNCERTAIN — Kandidat 2: G4)
- Forbidden words absent in REJECT/UNCERTAIN messages
"""

import io
import cv2
import numpy as np
import pytest
from PIL import Image

from ai.inference.domain_validator import ColonoscopyDomainValidator, DomainDecision


@pytest.fixture
def validator():
    return ColonoscopyDomainValidator()


def test_colonoscopy_with_timestamp_and_device_info_accepted(validator):
    """Regression test for bkai_000146: Colonoscopy with OSD text and folds must be ACCEPTED."""
    img = np.full((512, 512, 3), [195, 80, 75], dtype=np.uint8)
    cv2.circle(img, (256, 256), 200, (215, 105, 90), -1)  # Lumen depth
    cv2.circle(img, (256, 256), 70, (80, 30, 25), -1)     # Lumen center
    cv2.circle(img, (310, 290), 50, (175, 65, 60), -1)    # Polyp lesion
    cv2.circle(img, (270, 240), 6, (255, 255, 250), -1)   # Specular glint
    cv2.ellipse(img, (256, 200), (180, 40), 15, 0, 180, (160, 55, 50), 3)  # Fold
    # Text overlay from endoscope (BKAI metadata)
    cv2.putText(img, "2021/08/14 11:32:04", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(img, "OLYMPUS CF-H185L", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
    pil_img = Image.fromarray(img, mode="RGB")

    result = validator.validate_image(pil_img)
    assert result.decision == DomainDecision.ACCEPT
    assert result.confidence >= 0.55


def test_flat_raw_meat_prevented_from_inference(validator):
    """Flat uniform raw meat without endoscopic lighting/glints must NOT be ACCEPTED."""
    img = np.full((512, 512, 3), [185, 65, 55], dtype=np.uint8)
    cv2.circle(meat := img, (256, 256), 180, (200, 80, 65), -1)
    pil_img = Image.fromarray(img, mode="RGB")

    result = validator.validate_image(pil_img)
    # Must be UNCERTAIN (or REJECT), never ACCEPT
    assert result.decision != DomainDecision.ACCEPT


def test_colonoscopy_with_polyp_accepted(validator):
    """Colonoscopy with a visible polyp lesion must be ACCEPTED."""
    img = np.full((512, 512, 3), [195, 80, 75], dtype=np.uint8)  # Mucosal pink
    cv2.circle(img, (256, 256), 200, (215, 105, 90), -1)  # Lumen depth
    cv2.circle(img, (310, 290), 50, (175, 65, 60), -1)    # Polyp lesion
    cv2.circle(img, (270, 240), 6, (255, 255, 250), -1)   # Specular glint
    pil_img = Image.fromarray(img, mode="RGB")

    result = validator.validate_image(pil_img)
    assert result.decision == DomainDecision.ACCEPT
    assert result.confidence >= 0.65
    assert result.metrics["mucosal_ratio"] >= 0.60


def test_normal_colonoscopy_without_polyp_accepted(validator):
    """Normal colonoscopy mucosa (no polyp present) must be ACCEPTED."""
    img = np.full((512, 512, 3), [190, 85, 80], dtype=np.uint8)
    cv2.circle(img, (256, 256), 230, (205, 100, 90), -1)
    cv2.circle(img, (220, 220), 5, (255, 255, 245), -1)
    pil_img = Image.fromarray(img, mode="RGB")

    result = validator.validate_image(pil_img)
    assert result.decision == DomainDecision.ACCEPT
    assert result.confidence >= 0.65


def test_colonoscopy_with_circular_vignetting_accepted(validator):
    """Colonoscopy with dark circular camera aperture must be ACCEPTED."""
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    mask = np.zeros((512, 512), dtype=np.uint8)
    cv2.circle(mask, (256, 256), 210, 255, -1)
    tissue = np.full((512, 512, 3), [200, 90, 85], dtype=np.uint8)
    cv2.circle(tissue, (256, 256), 160, (220, 110, 95), -1)
    cv2.circle(tissue, (300, 260), 40, (180, 70, 65), -1)
    img[mask == 255] = tissue[mask == 255]
    pil_img = Image.fromarray(img, mode="RGB")

    result = validator.validate_image(pil_img)
    assert result.decision == DomainDecision.ACCEPT
    assert result.metrics["active_ratio"] < 1.0


def test_human_face_portrait_rejected(validator):
    """Human face / portrait photo must be REJECTED."""
    img = np.full((512, 512, 3), [180, 180, 190], dtype=np.uint8)  # Wall background
    img[380:, :] = [40, 60, 160]  # Blue shirt (cool hue)
    cv2.circle(img, (256, 200), 130, [30, 20, 15], -1)  # Hair
    cv2.ellipse(img, (256, 220), (80, 110), 0, 0, 360, [225, 180, 150], -1)  # Skin face
    pil_img = Image.fromarray(img, mode="RGB")

    result = validator.validate_image(pil_img)
    assert result.decision == DomainDecision.REJECT
    assert "tidak sesuai" in result.message.lower()


def test_food_pizza_rejected(validator):
    """Food image (pizza on plate with green olives/veggies) must be REJECTED."""
    img = np.full((512, 512, 3), [240, 240, 240], dtype=np.uint8)  # White plate
    cv2.circle(img, (256, 256), 200, (215, 175, 45), -1)  # Cheese/crust
    cv2.circle(img, (200, 200), 25, (40, 130, 40), -1)     # Green topping
    cv2.circle(img, (300, 220), 30, (30, 120, 35), -1)     # Green topping
    pil_img = Image.fromarray(img, mode="RGB")

    result = validator.validate_image(pil_img)
    assert result.decision == DomainDecision.REJECT


def test_landscape_rejected(validator):
    """Outdoor landscape (blue sky + green grass) must be REJECTED."""
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    img[:256, :] = [70, 140, 230]  # Blue sky
    img[256:, :] = [40, 160, 50]   # Green grass
    pil_img = Image.fromarray(img, mode="RGB")

    result = validator.validate_image(pil_img)
    assert result.decision == DomainDecision.REJECT
    assert result.metrics["cool_ratio"] > 0.15


def test_document_text_rejected(validator):
    """Text document / book page / screenshot must NOT be ACCEPTED.
    Note: Kandidat 2 — a purely achromatic (grayscale) document image hits the G4
    grayscale gate first → UNCERTAIN (hitam-putih). It is correctly blocked from inference.
    """
    img = np.full((512, 512, 3), 250, dtype=np.uint8)
    for y in range(40, 480, 20):
        cv2.line(img, (40, y), (460, y), (20, 20, 20), 2)
    pil_img = Image.fromarray(img, mode="RGB")

    result = validator.validate_image(pil_img)
    # Must never be ACCEPT; REJECT or UNCERTAIN both acceptable (blocked from inference)
    assert result.decision != DomainDecision.ACCEPT


def test_vehicle_car_rejected(validator):
    """Vehicle / car on asphalt road must be REJECTED."""
    img = np.full((512, 512, 3), [100, 100, 105], dtype=np.uint8)
    cv2.rectangle(img, (100, 200), (412, 360), (220, 20, 30), -1)  # Red car body
    cv2.rectangle(img, (160, 160), (350, 220), (120, 180, 200), -1)  # Windshield
    cv2.circle(img, (160, 360), 40, (20, 20, 20), -1)
    cv2.circle(img, (350, 360), 40, (20, 20, 20), -1)
    pil_img = Image.fromarray(img, mode="RGB")

    result = validator.validate_image(pil_img)
    assert result.decision == DomainDecision.REJECT


def test_medical_non_colonoscopy_xray_uncertain(validator):
    """Grayscale medical images (Chest X-ray / Brain MRI) must be UNCERTAIN (Kandidat 2: G4 grayscale → UNCERTAIN)."""
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    cv2.ellipse(img, (256, 256), (180, 220), 0, 0, 360, (140, 140, 140), -1)
    cv2.circle(img, (200, 220), 60, (60, 60, 60), -1)
    cv2.circle(img, (312, 220), 60, (60, 60, 60), -1)
    pil_img = Image.fromarray(img, mode="RGB")

    result = validator.validate_image(pil_img)
    assert result.decision == DomainDecision.UNCERTAIN
    assert result.metrics["mean_chroma"] < 10.0
    assert "hitam-putih" in result.message.lower() or "jelas" in result.message.lower()


def test_animal_rejected(validator):
    """Animal image (brown/black fur with outdoor grass) must be REJECTED."""
    img = np.full((512, 512, 3), [50, 150, 60], dtype=np.uint8)  # Grass background
    cv2.circle(img, (256, 256), 180, (110, 70, 40), -1)  # Brown animal fur
    pil_img = Image.fromarray(img, mode="RGB")

    result = validator.validate_image(pil_img)
    assert result.decision == DomainDecision.REJECT


def test_severely_underexposed_image_uncertain(validator):
    """Severely underexposed / dark ambiguous image must be marked UNCERTAIN."""
    img = np.full((512, 512, 3), [40, 20, 20], dtype=np.uint8)
    cv2.circle(img, (256, 256), 100, (55, 28, 24), -1)
    pil_img = Image.fromarray(img, mode="RGB")

    result = validator.validate_image(pil_img)
    assert result.decision == DomainDecision.UNCERTAIN
    assert "pencahayaan" in result.message.lower() or "jelas" in result.message.lower()


def test_small_dimension_rejected(validator):
    """Image with dimensions below minimum threshold must be REJECTED."""
    img = Image.new("RGB", (64, 64), color=(200, 90, 85))
    result = validator.validate_image(img)
    assert result.decision == DomainDecision.REJECT
    assert "tidak sesuai" in result.message.lower() or "kolonoskopi" in result.message.lower()


def test_extreme_aspect_ratio_rejected(validator):
    """Image with extreme banner aspect ratio must be REJECTED."""
    img = Image.new("RGB", (600, 150), color=(200, 90, 85))
    result = validator.validate_image(img)
    assert result.decision == DomainDecision.REJECT
    # Kandidat 2: all REJECT use unified message "Citra tidak sesuai..."
    assert "tidak sesuai" in result.message.lower() or "kolonoskopi" in result.message.lower()


def test_corrupted_bytes_rejected(validator):
    """Corrupted bytes must be REJECTED safely without unhandled exceptions."""
    result = validator.validate_bytes(b"not an image at all")
    assert result.decision == DomainDecision.REJECT


def test_grayscale_image_uncertain(validator):
    """Pure grayscale image (R=G=B for all pixels) must be UNCERTAIN with 'hitam-putih' message (Kandidat 2 G4)."""
    # Create a pure grayscale image (R=G=B, so mean_chroma ≈ 0 and mean_s ≈ 0)
    gray_val = 128
    img = Image.new("RGB", (512, 512), color=(gray_val, gray_val, gray_val))
    result = validator.validate_image(img)
    assert result.decision == DomainDecision.UNCERTAIN
    assert "hitam-putih" in result.message.lower()


_FORBIDDEN_WORDS = ["makanan", "daging", "karang", "spektrum warna", "x-ray", "mri", "non-endoskopi", "bukan merupakan"]


def _make_reject_cases(v):
    """Generate images expected to be REJECT."""
    cases = []
    # Landscape
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    img[:256, :] = [70, 140, 230]
    img[256:, :] = [40, 160, 50]
    cases.append(("landscape", Image.fromarray(img, "RGB")))
    # Document
    img = np.full((512, 512, 3), 250, dtype=np.uint8)
    for y in range(40, 480, 20):
        cv2.line(img, (40, y), (460, y), (20, 20, 20), 2)
    cases.append(("document", Image.fromarray(img, "RGB")))
    return cases


def _make_uncertain_cases(v):
    """Generate images expected to be UNCERTAIN."""
    cases = []
    # Underexposed
    img = np.full((512, 512, 3), [40, 20, 20], dtype=np.uint8)
    cv2.circle(img, (256, 256), 100, (55, 28, 24), -1)
    cases.append(("underexposed", Image.fromarray(img, "RGB")))
    # Grayscale
    cases.append(("grayscale", Image.new("RGB", (512, 512), color=(128, 128, 128))))
    return cases


def test_reject_message_no_forbidden_words(validator):
    """REJECT messages must not contain forbidden clinical/non-medical object words."""
    for name, img in _make_reject_cases(validator):
        result = validator.validate_image(img)
        if result.decision == DomainDecision.REJECT:
            msg_lower = result.message.lower()
            for word in _FORBIDDEN_WORDS:
                assert word not in msg_lower, (
                    f"REJECT message for '{name}' contains forbidden word '{word}': {result.message!r}"
                )


def test_uncertain_message_no_forbidden_words(validator):
    """UNCERTAIN messages must not contain forbidden clinical/non-medical object words."""
    for name, img in _make_uncertain_cases(validator):
        result = validator.validate_image(img)
        if result.decision == DomainDecision.UNCERTAIN:
            msg_lower = result.message.lower()
            for word in _FORBIDDEN_WORDS:
                assert word not in msg_lower, (
                    f"UNCERTAIN message for '{name}' contains forbidden word '{word}': {result.message!r}"
                )

