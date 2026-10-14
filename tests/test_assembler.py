import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import assembler


class TestAssembler(unittest.TestCase):
    def test_known_encodings(self):
        cases = {
            "addi x1, x0, 1": 0x00100093,
            "lui x2, 0x80000": 0x80000137,
            "lw x1, 0(x2)": 0x00012083,
            "sw x1, 0(x2)": 0x00112023,
            "jal x0, 0": 0x0000006F,
            "bne x1, x0, -4": 0xFE009EE3,
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                ins, labels = assembler.parse_source(source)
                self.assertEqual(assembler.encode_instruction(ins[0], labels), expected)

    def test_label_resolution_backward(self):
        source = """
_start:
    addi x1, x0, 1
loop:
    addi x1, x1, -1
    bne x1, x0, loop
"""
        words, labels = assembler.assemble_text(source)
        self.assertEqual(labels["loop"], 4)
        self.assertEqual(len(words), 3)
        self.assertEqual(words[2], 0xFE009EE3)

    def test_label_resolution_forward(self):
        source = """
    beq x0, x0, there
    addi x1, x0, 1
there:
    jal x0, there
"""
        words, labels = assembler.assemble_text(source)
        self.assertEqual(labels["there"], 8)
        # From PC 0 to PC 8 is +8.
        self.assertEqual(words[0], 0x00000463)
        self.assertEqual(words[2], 0x0000006F)

    def test_rv32e_register_limit(self):
        with self.assertRaises(assembler.AssemblerError):
            assembler.assemble_text("addi x16, x0, 1")

    def test_immediate_range(self):
        with self.assertRaises(assembler.AssemblerError):
            assembler.assemble_text("addi x1, x0, 2048")

    def test_shift_is_rejected_for_this_core(self):
        with self.assertRaises(assembler.AssemblerError):
            assembler.assemble_text("slli x1, x1, 1")

    def test_malformed_operand_lists_are_rejected(self):
        for source in ("addi x1,, x0, 1", "addi x1, x0, 1,", "add x1 x2, x3"):
            with self.subTest(source=source):
                with self.assertRaises(assembler.AssemblerError):
                    assembler.assemble_text(source)

    def test_duplicate_labels_are_rejected(self):
        with self.assertRaises(assembler.AssemblerError):
            assembler.assemble_text("again:\n  addi x1, x0, 0\nagain:\n  jal x0, again")


    def test_all_control_flow_targets_resolve_to_instruction_boundaries(self):
        source = (ROOT / "sw" / "game.s").read_text(encoding="utf-8")
        instructions, labels = assembler.parse_source(source)
        words, _ = assembler.assemble_text(source)

        def sext(value, bits):
            sign = 1 << (bits - 1)
            return (value ^ sign) - sign

        for ins, word in zip(instructions, words):
            if ins.mnemonic in {"beq", "bne", "bltu"} and ins.operands[2] in labels:
                imm = (((word >> 31) & 1) << 12) | (((word >> 7) & 1) << 11) | (((word >> 25) & 0x3F) << 5) | (((word >> 8) & 0xF) << 1)
                target = ins.pc + sext(imm, 13)
                self.assertEqual(target, labels[ins.operands[2]], ins.source)
            elif ins.mnemonic == "jal" and ins.operands[1] in labels:
                imm = (((word >> 31) & 1) << 20) | (((word >> 12) & 0xFF) << 12) | (((word >> 20) & 1) << 11) | (((word >> 21) & 0x3FF) << 1)
                target = ins.pc + sext(imm, 21)
                self.assertEqual(target, labels[ins.operands[1]], ins.source)

    def test_lfsr_nonzero_period_is_255(self):
        def step(state):
            feedback = state & 0x80
            state = (state * 2) & 0xFF
            if feedback:
                state ^= 0x1D
            return state
        state = 1
        seen = set()
        while state not in seen:
            seen.add(state)
            state = step(state)
        self.assertEqual(len(seen), 255)
        self.assertEqual(state, 1)

    def test_clock_cycle_constants(self):
        self.assertEqual(((0x262 << 12) + 0x5A0), 2_500_000)
        self.assertEqual(((0x4787 << 12) - 1856), 75_000_000)
        self.assertEqual(((0x131 << 12) + 720), 1_250_000)
        self.assertEqual(((0xBEC << 12) - 992), 12_500_000)
        self.assertEqual(((0x17D8 << 12) - 1984), 25_000_000)
        self.assertEqual(((0x95030 << 12) - 1792), 2_500_000_000)

    def test_game_program_assembles_and_fits_ram(self):
        source_path = ROOT / "sw" / "game.s"
        words, labels = assembler.assemble_text(source_path.read_text(encoding="utf-8"))
        self.assertEqual(len(words), 136)
        self.assertLessEqual(len(words), 512)
        self.assertIn("_start", labels)
        self.assertTrue(all(0 <= word <= 0xFFFFFFFF for word in words))
        # All label-relative branch/jump encodings were resolved by the assembler.
        output = ROOT / "sw" / "game.hex"
        lines = output.read_text(encoding="ascii").splitlines()
        self.assertEqual(len(lines), len(words))
        self.assertEqual([int(line, 16) for line in lines], words)
        self.assertTrue(all(len(line) == 8 and all(c in "0123456789abcdefABCDEF" for c in line) for line in lines))

    def test_target_timestamp_latch_is_tied_to_led_write(self):
        rtl = (ROOT / "rtl" / "pochoco_periph.v").read_text(encoding="utf-8")
        self.assertIn("target_start_counter_q <= cycle_counter_q", rtl)
        self.assertIn("4'b0001, 4'b0010, 4'b0100, 4'b1000", rtl)
        self.assertIn("6'd4: rdata_o <= target_start_counter_q", rtl)

    def test_exact_cycle_average_rounding(self):
        # Ten measurements from 0.1 s through 1.0 s average to 0.55 s,
        # which is 5.5 tenths and rounds half-up to 6 tenths.
        cycles_per_tenth = 2_500_000
        durations = [i * cycles_per_tenth for i in range(1, 11)]
        avg_tenths = (sum(durations) + 12_500_000) // 25_000_000
        self.assertEqual(avg_tenths, 6)
        self.assertEqual(sum([i for i in range(1, 11)]), 55)


if __name__ == "__main__":
    unittest.main()
