import json
import pytest

pytestmark = pytest.mark.api_exploration


def test_response_shape_capture():
    sample_response = {
        "example": "paste real response here if needed"
    }

    print(json.dumps(sample_response, indent=2, ensure_ascii=False))
    assert isinstance(sample_response, dict)
