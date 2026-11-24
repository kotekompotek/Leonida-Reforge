"""Unit tests for runtime/test/shaders/mullit_readback.py."""

from __future__ import annotations

import math
import struct
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "runtime" / "test" / "shaders"))

import mullit_readback as mr  # noqa: E402


def f32_to_u32(val: float) -> int:
    try:
        return struct.unpack("<I", struct.pack("<f", val))[0]
    except OverflowError:
        return (mr.SIGN if math.copysign(1.0, val) < 0 else 0) | mr.INF


def u32_to_f32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits))[0]


class TestMullitReadback(unittest.TestCase):
    def test_gate_and_light_off_cases(self) -> None:
        self.assertEqual(mr.lighting_product(mr.ONE, mr.ONE, 0), mr.LIGHT_OFF)
        self.assertEqual(mr.lighting_product(mr.ONE, mr.ONE, mr.MIN_NORMAL - 1), mr.LIGHT_OFF)
        self.assertEqual(mr.lighting_product(mr.ONE, mr.LIGHT_OFF, mr.ONE), mr.LIGHT_OFF)
        self.assertEqual(mr.lighting_product(mr.ONE, mr.SIGN | mr.INF, mr.ONE), mr.LIGHT_OFF)

    def test_zero_subnormal_inf_and_nan(self) -> None:
        self.assertEqual(mr.lighting_product(0, mr.ONE, mr.ONE), 0)
        self.assertEqual(mr.lighting_product(mr.ONE, mr.SIGN | 1, mr.ONE), 0)
        self.assertEqual(mr.lighting_product(0x7FC01234, mr.ONE, mr.ONE), 0x7FC01234)
        self.assertEqual(mr.lighting_product(mr.INF, mr.SIGN | mr.ONE, mr.ONE), mr.SIGN | mr.INF)

    def test_normal_products_and_halfway_rounding(self) -> None:
        for x, y, gate in mr.operand_triples():
            got = mr.lighting_product(x, y, gate)
            if got == mr.LIGHT_OFF:
                continue
            if min(x & ~mr.SIGN, y & ~mr.SIGN) < mr.MIN_NORMAL:
                self.assertEqual(got, 0)
                continue
            if (x & ~mr.SIGN) > mr.INF:
                self.assertEqual(got, x)
                continue
            fx, fy = u32_to_f32(x), u32_to_f32(y)
            if abs(fx) >= u32_to_f32(mr.MIN_NORMAL) and abs(fy) >= u32_to_f32(mr.MIN_NORMAL):
                prod = fx * fy
                if not math.isinf(prod) and abs(prod) >= u32_to_f32(mr.MIN_NORMAL):
                    self.assertEqual(got, f32_to_u32(prod))

        self.assertEqual(mr.lighting_product(0x3FC00000, mr.ONE + 1, mr.ONE), 0x3FC00002)
        self.assertEqual(mr.lighting_product(0x3FC00000, mr.ONE + 3, mr.ONE), 0x3FC00004)


if __name__ == "__main__":
    unittest.main()
