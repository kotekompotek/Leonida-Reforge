"""Unit tests for runtime/test/shaders/probe_signed_zero.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "runtime" / "test" / "shaders"))

import probe_signed_zero as psz  # noqa: E402


class TestProbeSignedZero(unittest.TestCase):
    def test_module_template_formats_both_image_formats(self) -> None:
        for fmt in ("Unknown", "Rgba32f"):
            text = psz.MODULE.format(image_format=fmt)
            self.assertIn("OpExecutionMode %main SignedZeroInfNanPreserve 32", text)
            self.assertIn(f"OpTypeImage %f 2D 0 0 0 2 {fmt}", text)

    def test_main_exit_codes_for_pass_skip_and_fail(self) -> None:
        for codes, expected in (
            ([0, 0, 0, 0, 0, 0], 0),
            ([0, 0, 0, 0, 0, 77], 77),
            ([0, 0, 1, 0, 0, 77], 1),
        ):
            side_effect = [mock.Mock(returncode=c) for c in codes]
            with mock.patch.object(sys, "argv", ["probe_signed_zero.py", "vk_store_test"]):
                with mock.patch.object(psz.subprocess, "run", side_effect=side_effect):
                    self.assertEqual(psz.main(), expected)


if __name__ == "__main__":
    unittest.main()
