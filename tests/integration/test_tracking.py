from typing import List

import pytest

from core import interface
from core.model import BBox, Detection, Frame, Object


@pytest.fixture
def make_frames() -> List[Frame]:

    frames = [
        Frame(
            0,
            [
                Detection(BBox(*[10, 20, 30, 40]), 1.0, 1, 0),
                Detection(BBox(*[15, 25, 35, 45]), 0.8, 2, 0),
                Detection(BBox(*[20, 30, 40, 50]), 0.1, 1, 0),
                Detection(BBox(*[25, 35, 45, 55]), 0.5, 1, 0),
            ],
        ),
        Frame(
            1,
            [
                Detection(BBox(*[10, 20, 30, 40]), 1.0, 1, 1),
                Detection(BBox(*[15, 25, 35, 45]), 0.8, 2, 1),
                Detection(BBox(*[20, 30, 40, 50]), 0.1, 1, 1),
                Detection(BBox(*[25, 35, 45, 55]), 0.5, 1, 1),
            ],
        ),
        Frame(
            2,
            [
                Detection(BBox(*[10, 20, 30, 40]), 1.0, 1, 2),
                Detection(BBox(*[15, 25, 35, 45]), 0.8, 2, 2),
                Detection(BBox(*[20, 30, 40, 50]), 0.1, 1, 2),
                Detection(BBox(*[25, 35, 45, 55]), 0.5, 1, 2),
            ],
        ),
    ]
    return frames


@pytest.mark.usefixtures("tracing_api")
def test_to_track(make_frames: List[Frame]):

    frames = make_frames

    objects = interface.to_track(frames)

    assert objects != None
    assert isinstance(objects[0], Object)
    assert isinstance(objects[0]._detections[0], Detection)
    assert isinstance(objects[0]._detections[0].bbox, BBox)