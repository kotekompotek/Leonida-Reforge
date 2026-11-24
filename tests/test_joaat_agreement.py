"""Two joaat contracts, each pinned: the dictionary rule of tools/hashdict.py and the mod rule of mods.h.

    python -I tests/test_joaat_agreement.py

Each tool carries its own copy of Jenkins one-at-a-time, so nothing stopped one of them from encoding
the name differently. Two did: audio_config hashed the lowercased UTF-8 bytes, and world_names encoded
to UTF-8 first and then lower-cased the bytes (bytes.lower() only folds ASCII). Both gave a different
32-bit hash for any non-ASCII character, which surfaces as a stream id no bank stores or a name hash
that never resolves, with no error anywhere.

There are two rules on purpose (docs/modding.md, "Name hashes"):

* the dictionary contract, ``hashdict.joaat``: Unicode lower-casing, then Latin-1 bytes (a character
  still above U+00FF after lower-casing becomes ``?``). Every copy in tools/ is compared with it unless
  MOD_CONTRACT names it, so a new copy is held to this rule by default;
* the mod contract, ``runtime/src/mods.h`` ``joaat`` and ``tools/leonida_mods.py`` ``joaat``: the
  UTF-8 bytes mod.json holds, with ASCII A-Z lower-cased and every other byte unchanged. It is checked
  against MOD_VECTORS, whose hashes come from the byte-level reference below, never from either
  implementation; runtime/test/mods_test.cpp checks the C++ joaat against the same table.

The two agree on ASCII names and hash different bytes for every non-ASCII one; the tests assert that the
hashes differ on the synthetic names rather than skip them. Neither rule establishes how the game hashes a
non-ASCII model name.

Synthetic names only; no game data.
"""
import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
MODS_TEST_CPP = os.path.join(ROOT, "runtime", "test", "mods_test.cpp")
for path in (ROOT, TOOLS):
    if path not in sys.path:
        sys.path.insert(0, path)

import hashdict  # noqa: E402

# ASCII names, then names with a non-ASCII character: "é" is one Latin-1 byte (0xE9) and two UTF-8
# bytes (0xC3 0xA9), and "ÉLÉGIE" also tells text.lower() apart from lower-casing the encoded bytes.
NAMES = [
    "adder", "plain_name", "burn", "boardwalk",
    "café", "Café", "Señor", "Crème Brûlée", "ÉLÉGIE", "Radio_LosSantos_Café",
]

# The dictionary consumers a reviewer would expect here: a rename must not turn the loop below into a
# test of nothing.
EXPECTED = ("anim_index", "audio_config", "awc_names", "hashdict", "mission_tables", "world_names")

# The copies that follow the mod contract instead, with the reason. Anything not listed here is a
# dictionary consumer.
MOD_CONTRACT = {
    "leonida_mods": "hashes mod.json names as the C++ mod runtime does (runtime/src/mods.h)",
}

# Published Jenkins one-at-a-time values over raw bytes (no lower-casing), to check one_at_a_time() itself.
ONE_AT_A_TIME_ANCHORS = (
    (b"a", 0xCA2E9442),
    (b"The quick brown fox jumps over the lazy dog", 0x519E91F5),
)

# The mod contract's synthetic vectors: (name, the bytes it hashes, hash). The bytes are the name's UTF-8
# with A-Z lower-cased, written out by hand; each hash was computed from them with one_at_a_time() and,
# separately, with a C implementation of the published algorithm, and agrees with ONE_AT_A_TIME_ANCHORS.
# Names are escapes so the source cannot change their code points. runtime/test/mods_test.cpp holds the
# same rows in kModJoaatVectors.
MOD_VECTORS = (
    ("plain_name", b"plain_name", 0x0C082AF0),
    ("Mixed_CASE_09", b"mixed_case_09", 0x0A605979),
    ("café", b"caf\xc3\xa9", 0x9096ADF2),                     # café: é is two UTF-8 bytes
    ("CAFÉ", b"caf\xc3\x89", 0xC7E69C9D),                     # CAFÉ: É is not folded to é
    ("Ωmega", b"\xce\xa9mega", 0xFDCD0371),                   # Ωmega: outside Latin-1, not folded
    ("名前", b"\xe5\x90\x8d\xe5\x89\x8d", 0xA395EABD),     # 名前: CJK, three bytes each
    ("smile_\U0001F600", b"smile_\xf0\x9f\x98\x80", 0x7F0B2EDE),   # smile_ + U+1F600, written as UTF-8, no escape
)

# The JSON surrogate-pair limitation (docs/modding.md, "Name hashes"): the runtime's JSON reader turns the
# escaped smile_ + U+1F600 into these CESU-8 bytes, not the UTF-8 of the last vector.
RUNTIME_READS_ESCAPED_PAIR_AS = b"smile_\xed\xa0\xbd\xed\xb8\x80"
RUNTIME_HASH_OF_ESCAPED_PAIR = 0x579A5A35


def one_at_a_time(data):
    """Jenkins one-at-a-time over bytes exactly as given: no encoding, no lower-casing."""
    h = 0
    for byte in data:
        h = (h + byte) & 0xFFFFFFFF
        h = (h + (h << 10)) & 0xFFFFFFFF
        h ^= h >> 6
    h = (h + (h << 3)) & 0xFFFFFFFF
    h ^= h >> 11
    return (h + (h << 15)) & 0xFFFFFFFF


def mod_contract_bytes(name):
    """The bytes the mod contract hashes: UTF-8, then A-Z lower-cased (bytes.lower() folds ASCII only)."""
    return name.encode("utf-8").lower()


def string_hash_copies():
    """{module name: function} for every ``def joaat(``/``def joaat32(`` that takes a string.

    ``tools/save_keys.py`` defines ``joaat(data, seed=0)`` over bytes with a seed for the composition
    probe; it is a different hash and is covered by tests/test_save_keys.py.
    """
    copies = {}
    for filename in sorted(os.listdir(TOOLS)):
        if not filename.endswith(".py"):
            continue
        with open(os.path.join(TOOLS, filename), encoding="utf-8") as handle:
            source = handle.read()
        for match in re.finditer(r"^def (joaat32|joaat)\(\s*([A-Za-z_]\w*)", source, re.M):
            if match.group(2) == "data":
                continue
            module = __import__(filename[:-3])
            copies[filename[:-3]] = getattr(module, match.group(1))
    return copies


def c_string_literal(text):
    """The bytes of the C++ string literal body ``text`` (plain ASCII, ``\\xNN``, ``\\\\`` and ``\\"``).

    A hex escape is read greedily, as a C++ compiler reads it, so ``caf\\xC3\\xA9e`` fails here as it
    would there instead of silently giving other bytes.
    """
    out = bytearray()
    i = 0
    while i < len(text):
        c = text[i]
        if c != "\\":
            out += c.encode("ascii")
            i += 1
            continue
        e = text[i + 1:i + 2]
        if e in ("\\", '"'):
            out += e.encode("ascii")
            i += 2
        elif e == "x":
            digits = re.match(r"[0-9A-Fa-f]*", text[i + 2:]).group(0)
            if not digits or int(digits, 16) > 0xFF:
                raise ValueError(f"\\x{digits} is not one byte in {text!r}")
            out.append(int(digits, 16))
            i += 2 + len(digits)
        else:
            raise ValueError(f"unsupported escape \\{e} in {text!r}")
    return bytes(out)


def cpp_mod_vectors():
    """[(name bytes, folded bytes, hash)] from kModJoaatVectors in runtime/test/mods_test.cpp."""
    with open(MODS_TEST_CPP, encoding="utf-8") as handle:
        source = handle.read()
    table = re.search(r"kModJoaatVectors\[\] = \{\n(.*?)\n\};", source, re.S)
    if not table:
        raise AssertionError("kModJoaatVectors not found in runtime/test/mods_test.cpp")
    literal = r'"((?:[^"\\]|\\.)*)"'
    row = re.compile(r"\{" + literal + r", " + literal + r", 0x([0-9A-Fa-f]{8})u\},")
    rows = []
    for line in table.group(1).splitlines():
        code = line.split("//")[0].strip()
        if not code:
            continue
        match = row.fullmatch(code)
        if not match:
            raise AssertionError(f"unreadable kModJoaatVectors row: {code}")
        rows.append((c_string_literal(match.group(1)), c_string_literal(match.group(2)), int(match.group(3), 16)))
    return rows


class JoaatAgreementTest(unittest.TestCase):
    def test_every_dictionary_copy_matches_the_pinned_dictionary(self):
        copies = string_hash_copies()
        for module in EXPECTED:
            self.assertIn(module, copies)
        self.assertFalse(set(EXPECTED) & set(MOD_CONTRACT), "a module cannot follow both contracts")
        for module, function in sorted(copies.items()):
            if module in MOD_CONTRACT:
                continue
            for name in NAMES:
                with self.subTest(copy=module, name=name):
                    self.assertEqual(function(name), hashdict.joaat(name),
                                     f"{module} hashes {name!r} differently from hashdict.joaat")

    def test_a_stream_id_is_the_name_hash_of_the_same_name(self):
        # The consequence of the bug: audio_config's id and the id awc_names recovers from a bank were
        # computed with two different encodings, so they could never match for an accented title.
        import audio_config
        import awc_names

        for title in ("Café", "Crème Brûlée", "Radio Los Santos", "plain_song"):
            with self.subTest(title=title):
                self.assertEqual(audio_config.title_stream_id(title),
                                 awc_names.joaat(audio_config.normalized_name(title)) & 0x1FFFFFFF)


class ModContractTest(unittest.TestCase):
    def test_the_reference_gives_the_published_values(self):
        for data, expected in ONE_AT_A_TIME_ANCHORS:
            with self.subTest(data=data):
                self.assertEqual(one_at_a_time(data), expected)

    def test_the_vectors_follow_the_byte_rule(self):
        for name, folded, expected in MOD_VECTORS:
            with self.subTest(name=name):
                self.assertEqual(mod_contract_bytes(name), folded)
                self.assertEqual(one_at_a_time(folded), expected)

    def test_every_mod_contract_copy_matches_the_vectors(self):
        copies = string_hash_copies()
        for module in MOD_CONTRACT:
            self.assertIn(module, copies, f"{module} is listed in MOD_CONTRACT but has no joaat")
            function = copies[module]
            for name, _, expected in MOD_VECTORS:
                with self.subTest(copy=module, name=name):
                    self.assertEqual(function(name), expected)
            for name in NAMES:
                with self.subTest(copy=module, name=name):
                    self.assertEqual(function(name), one_at_a_time(mod_contract_bytes(name)))

    def test_the_contracts_agree_on_ascii_and_differ_on_every_other_name(self):
        # ASCII is one byte per character under both rules and A-Z is the only folding that applies, so the
        # hashes are equal. A non-ASCII character is two to four UTF-8 bytes under the mod contract and one
        # Latin-1 byte (or "?") under the dictionary contract, so the hashed bytes, and here the hashes, differ.
        names = NAMES + [name for name, _, _ in MOD_VECTORS]
        copies = string_hash_copies()
        for module in MOD_CONTRACT:
            function = copies[module]
            for name in names:
                with self.subTest(copy=module, name=name):
                    if name.isascii():
                        self.assertEqual(function(name), hashdict.joaat(name))
                    else:
                        self.assertNotEqual(function(name), hashdict.joaat(name),
                                            "the UTF-8 and Latin-1 hashes of a non-ASCII name differ")

    def test_where_the_dictionary_contract_folds_more(self):
        # The dictionary contract lower-cases every character and replaces those still above U+00FF with "?";
        # the mod contract folds A-Z only and keeps every byte.
        self.assertEqual(hashdict.joaat("CAFÉ"), hashdict.joaat("café"))
        self.assertEqual(hashdict.joaat("Ωmega"), hashdict.joaat("?mega"))
        self.assertEqual(hashdict.joaat("名前"), hashdict.joaat("??"))
        self.assertEqual(hashdict.joaat("smile_\U0001F600"), hashdict.joaat("smile_?"))
        self.assertNotEqual(MOD_VECTORS[2][2], MOD_VECTORS[3][2], "café and CAFÉ hash apart under the mod contract")

    def test_the_cpp_test_has_the_same_vectors(self):
        rows = cpp_mod_vectors()
        expected = [(name.encode("utf-8"), folded, value) for name, folded, value in MOD_VECTORS]
        self.assertEqual(len(rows), len(MOD_VECTORS), "runtime/test/mods_test.cpp has a different row count")
        self.assertEqual(rows, expected, "kModJoaatVectors in runtime/test/mods_test.cpp differs from MOD_VECTORS")

    def test_a_cpp_hex_escape_is_read_as_the_compiler_reads_it(self):
        self.assertEqual(c_string_literal(r"caf\xC3\xA9"), b"caf\xc3\xa9")
        self.assertEqual(c_string_literal(r"\xCE\xA9mega"), b"\xce\xa9mega")
        with self.assertRaises(ValueError):
            c_string_literal(r"caf\xC3\xA9e")


class JsonSurrogatePairLimitationTest(unittest.TestCase):
    """A recorded limitation of the runtime's JSON reader, not a contract (docs/modding.md, "Name hashes").

    Python's json joins an escaped surrogate pair into one code point, so tools/leonida_mods.py hashes the
    UTF-8 bytes of U+1F600; the runtime's reader writes each half as its own three-byte sequence
    (runtime/test/mods_test.cpp records that). The two hashes differ, so no end-to-end parity is claimed for
    supplementary characters until the reader changes (a separate proposal).
    """

    MANIFEST = '{"archetype_swaps": [{"from": "smile_\\ud83d\\ude00", "to": "plain_name"}]}'

    def test_python_reads_the_pair_as_one_code_point(self):
        import leonida_mods

        data = json.loads(self.MANIFEST)
        self.assertEqual(data["archetype_swaps"][0]["from"], "smile_\U0001F600")
        mod = leonida_mods.validate_manifest(data, "m")
        self.assertEqual(mod.swaps[0].from_id, MOD_VECTORS[-1][2])

    def test_the_runtime_reading_hashes_differently(self):
        self.assertEqual(one_at_a_time(RUNTIME_READS_ESCAPED_PAIR_AS), RUNTIME_HASH_OF_ESCAPED_PAIR)
        self.assertNotEqual(RUNTIME_HASH_OF_ESCAPED_PAIR, MOD_VECTORS[-1][2])
        with open(MODS_TEST_CPP, encoding="utf-8") as handle:
            source = handle.read()
        # mods_test.cpp checks the reader against the same bytes and hash.
        self.assertIn(r'"smile_\xED\xA0\xBD\xED\xB8\x80"', source)
        self.assertIn(f"0x{RUNTIME_HASH_OF_ESCAPED_PAIR:08X}u", source)


if __name__ == "__main__":
    unittest.main()
