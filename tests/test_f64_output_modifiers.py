"""Check the result of output modifiers (omod, then clamp) on v_add_f64 by running the translated SPIR-V.

LLVM defines v_add_f64 as VOP3Inst<"v_add_f64", VOP3_Profile<VOP_F64_F64_F64>>; VOPProfile gives it HasClamp
(f64 is a modifier type) and HasOMod (its destination is floating point). runtime/test/shaders/ps_f64_mods.asm is
the matching GPU test. The translated module runs in tests/semantic/spirv_mini_interp.py, and the words written to
v[4:5] are compared with the ISA rule computed in Python, so the check does not depend on the SPIR-V's wording.
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

MODIFIERS = (
    ("", 1.0, False),
    ("mul:2", 2.0, False),
    ("mul:4", 4.0, False),
    ("div:2", 0.5, False),
    ("clamp", 1.0, True),
    ("clamp div:2", 0.5, True),
    ("mul:4 clamp", 4.0, True),
)
# (a, b): the GPU test's 0.75 + 0.5, whose low words are zero, a pair whose sum has a non-zero low word, and a
# negative sum, so that clamp's lower bound (0, not a negative number) decides the result.
INPUTS = ((0.75, 0.5), (1 / 3, 0.25), (-0.75, 0.25))
OLD = (0x11111111, 0x22222222)  # v[4:5] before the add, kept by a lane with EXEC off


def words(x):
    bits = struct.unpack("<Q", struct.pack("<d", x))[0]
    return bits & 0xFFFFFFFF, bits >> 32


def mods(x, scale=1.0, clamp=False):
    """The ISA rule: the output modifier scales first, then clamp limits the result to [0, 1]."""
    x *= scale
    return min(max(x, 0.0), 1.0) if clamp else x


def body(a, b, modifiers, exec_off=False):
    """a in v[0:1], b in v[6:7] (low word first); the sum goes to v[4:5]."""
    (a_lo, a_hi), (b_lo, b_hi) = words(a), words(b)
    lines = [f"v_mov_b32 v4, {OLD[0]:#x}", f"v_mov_b32 v5, {OLD[1]:#x}",
             f"v_mov_b32 v0, {a_lo:#x}", f"v_mov_b32 v1, {a_hi:#x}",
             f"v_mov_b32 v6, {b_lo:#x}", f"v_mov_b32 v7, {b_hi:#x}"]
    if exec_off:
        lines.append("s_mov_b64 exec, 0")
    lines.append(f"v_add_f64 v[4:5], v[0:1], v[6:7] {modifiers}".rstrip())
    if exec_off:
        lines.append("s_mov_b64 exec, -1")
    return "\n".join(lines)


def run_add(directory, text):
    """Return the module for `text` and v[4:5] after it (the listing's epilogue exports v3, so each word is copied
    there in turn)."""
    spv = translate_listing(Path(directory), text)
    got = tuple(run_fragment(translate_listing(Path(directory), f"{text}\nv_mov_b32 v3, v{r}"))["%out_mrt0"][0]
                for r in (4, 5))
    return spv, got


class F64OutputModifiersTest(unittest.TestCase):
    def test_add_f64_output_modifiers(self):
        with tempfile.TemporaryDirectory() as directory:
            for a, b in INPUTS:
                for modifiers, scale, clamp in MODIFIERS:
                    with self.subTest(a=a, b=b, modifiers=modifiers):
                        spv, got = run_add(directory, body(a, b, modifiers))
                        self.assertEqual(got, words(mods(a + b, scale, clamp)))
                        self.check_structure(spv, scale, clamp)

    def test_lane_with_exec_off_keeps_the_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            for modifiers, _scale, _clamp in MODIFIERS:
                with self.subTest(modifiers=modifiers):
                    _spv, got = run_add(directory, body(0.75, 0.5, modifiers, exec_off=True))
                    self.assertEqual(got, OLD)

    def check_structure(self, spv, scale, clamp):
        """What the values alone cannot show: no stray scale or clamp, and every f64 add and scale is rounded on its
        own (no_contraction decorates all float arithmetic)."""
        if scale == 1.0:
            self.assertNotRegex(spv, r"OpFMul %double")
        if not clamp:
            self.assertNotIn("FClamp", spv)
        ops = re.findall(r"(?m)^ *(%\w+) = Op(?:FAdd|FMul) %double ", spv)
        self.assertTrue(ops)
        for op in ops:
            self.assertRegex(spv, rf"(?m)^ *OpDecorate {op} NoContraction$")

    def test_gpu_fixture_expectation(self):
        """The words written in ps_f64_mods.asm follow from the ISA rule (omod, then clamp), computed in Python."""
        a, b = 0.75, 0.5
        want = tuple(words(v)[1] for v in (mods(a + b, 2.0), mods(a + b, clamp=True),
                                           mods(a + b, 0.5, True), mods(a - b, 4.0)))
        asm = (TEST_DIR.parent / "runtime" / "test" / "shaders" / "ps_f64_mods.asm").read_text(encoding="utf-8")
        line = re.search(r"Expected mrt0 bits: (.*)", asm).group(1)
        self.assertEqual(tuple(int(w, 16) for w in line.split(", ")), want)


if __name__ == "__main__":
    unittest.main()
