"""Unit tests for runtime/test/shaders/w64_graphics.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "runtime" / "test" / "shaders"))

import w64_graphics as wg  # noqa: E402


class TestW64GraphicsExpectations(unittest.TestCase):
    def test_coord_helpers(self) -> None:
        self.assertEqual((wg._x(0), wg._y(0)), (0, 0))
        self.assertEqual((wg._x(65), wg._y(65)), (1, 1))
        self.assertEqual(wg._on(7 * 64 + 5), 1)
        self.assertEqual(wg._on(0), 0)

    def test_tier_a_discard_and_permlane(self) -> None:
        self.assertEqual(wg._a_discard(0), (wg.CLEAR,) * 4)
        self.assertEqual(wg._a_discard(0 * 64 + 32), (32, 1, 2000, 1))
        self.assertEqual(wg._a_permlane(0), (1, 64, 0, 0))
        self.assertEqual(wg._a_swizzle(0), (65, 1, 0, 0))

    def test_tier_b_and_tier_c_expectations(self) -> None:
        self.assertEqual(wg._b_readfirstlane(5), (128, 277, 0, 0))
        self.assertEqual(wg._b_readlane_uniform(5), (128, 200, 0, 0))
        self.assertEqual(wg._b_ballot(1), (1, 0, 0, 0))
        self.assertEqual(wg._b_ballot(2), (0, 0, 0, 0))

        self.assertEqual(wg._c_bcnt(1), (None, 1, 0, 0))
        self.assertEqual(wg._c_lane_id(7), (None, None, 7, 0))
        self.assertEqual(wg._c_vote_else(7 * 64 + 5), (7, 1, 0, 0))
        self.assertEqual(wg._c_vote_else(0), (None, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
