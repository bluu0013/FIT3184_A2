import unittest

import _paths  # noqa: F401
from ecoguard_common import tags


class NormaliseQueryTests(unittest.TestCase):
    def test_dict_keeps_counts(self):
        self.assertEqual(tags.normalise_query({"Fox": 2, " feral  pig ": 1}), {"fox": 2, "feral pig": 1})

    def test_list_and_string_mean_count_one(self):
        self.assertEqual(tags.normalise_query(["Cat", "dog"]), {"cat": 1, "dog": 1})
        self.assertEqual(tags.normalise_query("cat"), {"cat": 1})

    def test_rejects_bad_input(self):
        for bad in ({}, [], {"fox": 0}, {"fox": -1}, {"fox": 1.5}, {"fox": True}, {"": 1}, [1], 7):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    tags.normalise_query(bad)


class MatchesTests(unittest.TestCase):
    def test_and_with_minimum_counts(self):
        record = {"feral pig": 1, "cane toad": 3, "fox": 2}
        self.assertTrue(tags.matches(record, {"fox": 2}))
        self.assertTrue(tags.matches(record, {"feral pig": 1, "cane toad": 3}))
        self.assertFalse(tags.matches(record, {"feral pig": 2}))
        self.assertFalse(tags.matches(record, {"fox": 1, "rabbit": 1}))  # AND, not OR

    def test_empty_record(self):
        self.assertFalse(tags.matches({}, {"fox": 1}))
        self.assertFalse(tags.matches(None, {"fox": 1}))


class ApplyTagEditTests(unittest.TestCase):
    def test_add(self):
        self.assertEqual(tags.apply_tag_edit({"fox": 1}, {"cat": 1}, 1), {"fox": 1, "cat": 1})

    def test_add_keeps_larger_count(self):
        self.assertEqual(tags.apply_tag_edit({"fox": 3}, {"fox": 1}, 1), {"fox": 3})
        self.assertEqual(tags.apply_tag_edit({"fox": 1}, {"fox": 4}, 1), {"fox": 4})

    def test_remove_ignores_missing(self):
        self.assertEqual(tags.apply_tag_edit({"fox": 1, "cat": 1}, {"fox": 1, "pig": 1}, 0), {"cat": 1})

    def test_does_not_mutate_input(self):
        current = {"fox": 1}
        tags.apply_tag_edit(current, {"cat": 1}, 1)
        self.assertEqual(current, {"fox": 1})

    def test_bad_operation(self):
        for op in (2, -1, "1", None, True):
            with self.subTest(op=op):
                with self.assertRaises(ValueError):
                    tags.apply_tag_edit({}, {"fox": 1}, op)


if __name__ == "__main__":
    unittest.main()
