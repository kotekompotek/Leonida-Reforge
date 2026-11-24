"""Check the result of output modifiers on v_cvt_f32_f64 by running the translated SPIR-V.

The translated module runs in tests/semantic/spirv_mini_interp.py, and the word written to v3 is compared with the
rule (convert to f32, scale by the output modifier, then clamp to [0, 1]) computed in Python and with the expected
words listed in the fixture, so the check does not depend on the SPIR-V's wording.
"""

import re
import struct
import sys
import tempfile
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
sys.path[:0] = [str(TEST_DIR.parent / "tools"), str(TEST_DIR), str(TEST_DIR / "semantic")]

from listing import translate_listing  # noqa: E402
from spirv_mini_interp import run_fragment  # noqa: E402

FIXTURE = TEST_DIR / "fixtures" / "f64_conversion.asm"
INPUT = 1.5  # the fixture's v[0:1]
MODIFIERS = (
    ("", 1.0, False),
    ("mul:2", 2.0, False),
    ("mul:4", 4.0, False),
    ("div:2", 0.5, False),
    ("clamp", 1.0, True),
    ("clamp div:2", 0.5, True),
)
OLD = 0x5A5A5A5A  # v3 before the conversion, kept by a lane with EXEC off


def f32_word(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


def expected(scale, clamp, value=INPUT):
    x = struct.unpack("<f", struct.pack("<f", value))[0] * scale
    return f32_word(min(max(x, 0.0), 1.0) if clamp else x)


def fixture_body():
    return "\n".join(line for line in FIXTURE.read_text(encoding="utf-8").splitlines() if not line.startswith(";"))


def run_conversion(directory, text):
    """Return the module for `text` and v3 after it (the listing's epilogue exports v3)."""
    spv = translate_listing(Path(directory), text)
    return spv, run_fragment(spv)["%out_mrt0"][0]


class F64ConversionTest(unittest.TestCase):
    def test_output_modifiers(self):
        with tempfile.TemporaryDirectory() as directory:
            for modifiers, scale, clamp in MODIFIERS:
                with self.subTest(modifiers=modifiers):
                    spv, got = run_conversion(directory, f"{fixture_body()} {modifiers}".rstrip())
                    self.assertEqual(got, expected(scale, clamp), f"{got:#010x}")
                    if scale == 1.0:
                        self.assertNotRegex(spv, r"OpFMul %float")
                    if not clamp:
                        self.assertNotIn("FClamp", spv)

    def test_negative_input(self):
        """-1.5: clamp must give +0.0 (its lower bound is 0); the fixture's 1.5 only reaches the upper bound."""
        text = fixture_body().replace("v_mov_b32 v1, 0x3ff80000", "v_mov_b32 v1, 0xbff80000")
        self.assertNotEqual(text, fixture_body())
        with tempfile.TemporaryDirectory() as directory:
            for modifiers, scale, clamp in MODIFIERS:
                with self.subTest(modifiers=modifiers):
                    _spv, got = run_conversion(directory, f"{text} {modifiers}".rstrip())
                    self.assertEqual(got, expected(scale, clamp, -1.5), f"{got:#010x}")

    def test_lane_with_exec_off_keeps_the_destination(self):
        cvt = "v_cvt_f32_f64_e64 v3, v[0:1]"
        with tempfile.TemporaryDirectory() as directory:
            for modifiers, _scale, _clamp in MODIFIERS:
                with self.subTest(modifiers=modifiers):
                    text = fixture_body().replace(cvt, f"v_mov_b32 v3, {OLD:#x}\ns_mov_b64 exec, 0\n{cvt}")
                    _spv, got = run_conversion(directory, f"{text} {modifiers}".rstrip() + "\ns_mov_b64 exec, -1")
                    self.assertEqual(got, OLD, f"{got:#010x}")

    def test_fixture_lists_the_expected_words(self):
        listed = dict(re.findall(r"(?m)^; (none|mul:2|mul:4|div:2|clamp|clamp div:2) +(0x[0-9a-f]{8})",
                                 FIXTURE.read_text(encoding="utf-8")))
        self.assertEqual({m or "none": expected(s, c) for m, s, c in MODIFIERS},
                         {m: int(w, 16) for m, w in listed.items()})


if __name__ == "__main__":
    unittest.main()
