import unittest

import _paths  # noqa: F401
from app.aggregate import counts_from_detections, frame_indices, merge_max


def det(label, conf):
    return {"label": label, "confidence": conf, "bbox": [0, 0, 1, 1]}


class CountTests(unittest.TestCase):
    def test_threshold_and_counting(self):
        found = [det("fox", 0.9), det("fox", 0.4), det("fox", 0.2), det("cat", 0.8)]
        self.assertEqual(counts_from_detections(found, 0.35), {"fox": 2, "cat": 1})

    def test_label_map_renames_and_drops(self):
        found = [det("domestic cat", 0.9), det("bird", 0.9)]
        mapped = counts_from_detections(found, 0.35, {"domestic cat": "cat", "bird": None})
        self.assertEqual(mapped, {"cat": 1})

    def test_labels_are_lower_cased(self):
        self.assertEqual(counts_from_detections([det("Feral Pig", 0.9)], 0.35), {"feral pig": 1})


class MergeTests(unittest.TestCase):
    def test_max_not_sum(self):
        self.assertEqual(merge_max([{"fox": 1}, {"fox": 2, "cat": 1}, {}]), {"fox": 2, "cat": 1})

    def test_empty(self):
        self.assertEqual(merge_max([]), {})


class FrameIndexTests(unittest.TestCase):
    def test_one_frame_per_ten_seconds(self):
        # 25 s at 30 fps = 750 frames -> t=0, 10, 20 s
        self.assertEqual(frame_indices(750, 30.0, 10), [0, 300, 600])

    def test_short_video_gets_first_frame(self):
        self.assertEqual(frame_indices(90, 30.0, 10), [0])

    def test_missing_fps_falls_back(self):
        self.assertEqual(frame_indices(600, 0, 10), [0, 250, 500])

    def test_empty_video(self):
        self.assertEqual(frame_indices(0, 30.0, 10), [])


if __name__ == "__main__":
    unittest.main()
