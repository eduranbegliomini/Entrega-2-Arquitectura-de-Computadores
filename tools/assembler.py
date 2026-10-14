#!/usr/bin/env python3
"""Small two-pass assembler for the RV32E subset used by this project.

It emits one 32-bit instruction word as eight hexadecimal digits per line.
It does not invoke an external RISC-V assembler.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

REG_RE = re.compile(r"x(\d+)$", re.IGNORECASE)
MEM_RE = re.compile(r"^(.+)\((x\d+)\)$", re.IGNORECASE)

SUPPORTED = {
    "lui", "addi", "andi", "xori", "add", "sub", "and", "xor",
    "lw", "sw", "beq", "bne", "bltu", "jal"
}
IGNORED_DIRECTIVES = {".section", ".text", ".global", ".globl", ".type", ".size"}

class AssemblerError(Exception):
    """Raised for invalid source or an unencodable instruction."""

@dataclass
class SourceInstruction:
    line_no: int
    source: str
    pc: int
    mnemonic: str
    operands: List[str]


def parse_number(value: str, context: str) -> int:
    value = value.strip().replace("_", "")
    try:
        # int(..., 0) handles decimal and 0x/0b prefixes; signed values work too.
        return int(value, 0)
    except ValueError as exc:
        raise AssemblerError(f"{context}: invalid integer literal {value!r}") from exc


def parse_reg(token: str, context: str) -> int:
    match = REG_RE.fullmatch(token.strip())
    if not match:
        raise AssemblerError(f"{context}: expected register x0..x15, got {token!r}")
    reg = int(match.group(1))
    if not 0 <= reg <= 15:
        raise AssemblerError(f"{context}: register x{reg} is outside RV32E range x0..x15")
    return reg


def signed_fits(value: int, bits: int) -> bool:
    return -(1 << (bits - 1)) <= value < (1 << (bits - 1))


def enc_i(opcode: int, rd: int, funct3: int, rs1: int, imm: int, context: str) -> int:
    if not signed_fits(imm, 12):
        raise AssemblerError(f"{context}: immediate {imm} does not fit signed 12 bits")
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode


def enc_r(rd: int, rs1: int, rs2: int, funct3: int, funct7: int = 0) -> int:
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | 0x33


def enc_s(rs2: int, rs1: int, imm: int, funct3: int, context: str) -> int:
    if not signed_fits(imm, 12):
        raise AssemblerError(f"{context}: store offset {imm} does not fit signed 12 bits")
    u = imm & 0xFFF
    return (((u >> 5) & 0x7F) << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | ((u & 0x1F) << 7) | 0x23


def enc_b(rs1: int, rs2: int, offset: int, funct3: int, context: str) -> int:
    if offset & 1:
        raise AssemblerError(f"{context}: branch target offset {offset} must be even")
    if not -(1 << 12) <= offset <= (1 << 12) - 2:
        raise AssemblerError(f"{context}: branch offset {offset} is outside -4096..4094")
    u = offset & 0x1FFF
    return (((u >> 12) & 1) << 31) | (((u >> 5) & 0x3F) << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (((u >> 1) & 0xF) << 8) | (((u >> 11) & 1) << 7) | 0x63


def enc_u(rd: int, imm: int, context: str) -> int:
    # Assembly syntax takes the raw 20-bit immediate, not the byte address.
    if not -(1 << 19) <= imm <= (1 << 20) - 1:
        raise AssemblerError(f"{context}: LUI immediate {imm} does not fit 20 bits")
    return ((imm & 0xFFFFF) << 12) | (rd << 7) | 0x37


def enc_j(rd: int, offset: int, context: str) -> int:
    if offset & 1:
        raise AssemblerError(f"{context}: JAL target offset {offset} must be even")
    if not -(1 << 20) <= offset <= (1 << 20) - 2:
        raise AssemblerError(f"{context}: JAL offset {offset} is outside -1048576..1048574")
    u = offset & 0x1FFFFF
    return (((u >> 20) & 1) << 31) | (((u >> 1) & 0x3FF) << 21) | (((u >> 11) & 1) << 20) | (((u >> 12) & 0xFF) << 12) | (rd << 7) | 0x6F


def split_operands(text: str) -> List[str]:
    # Current supported syntax has comma-separated operands and no nested expressions.
    return [part.strip() for part in text.split(",")]


def strip_comment(line: str) -> str:
    # '#' is the style used by the supplied .s files. Also accept ';'.
    return line.split("#", 1)[0].split(";", 1)[0].strip()


def parse_source(source: str) -> Tuple[List[SourceInstruction], Dict[str, int]]:
    instructions: List[SourceInstruction] = []
    labels: Dict[str, int] = {}
    pc = 0
    for line_no, raw in enumerate(source.splitlines(), start=1):
        text = strip_comment(raw)
        if not text:
            continue
        # Allow one or more labels before an instruction/directive.
        while ":" in text:
            left, right = text.split(":", 1)
            label = left.strip()
            if not re.fullmatch(r"[A-Za-z_.$][\w.$]*", label):
                break
            if label in labels:
                raise AssemblerError(f"line {line_no}: duplicate label {label!r}")
            labels[label] = pc
            text = right.strip()
            if not text:
                break
        if not text:
            continue
        if text.startswith("."):
            directive = text.split(None, 1)[0].lower()
            if directive not in IGNORED_DIRECTIVES:
                raise AssemblerError(f"line {line_no}: unsupported directive {directive!r}")
            continue
        parts = text.split(None, 1)
        mnemonic = parts[0].lower()
        if mnemonic not in SUPPORTED:
            raise AssemblerError(f"line {line_no}: unsupported instruction {mnemonic!r}; supported: {', '.join(sorted(SUPPORTED))}")
        operands = split_operands(parts[1]) if len(parts) > 1 else []
        instructions.append(SourceInstruction(line_no, raw.rstrip(), pc, mnemonic, operands))
        pc += 4
    return instructions, labels


def resolve_target(token: str, pc: int, labels: Dict[str, int], context: str) -> int:
    if token in labels:
        return labels[token] - pc
    # Numeric branch/JAL targets are accepted as relative offsets.
    return parse_number(token, context)


def encode_instruction(ins: SourceInstruction, labels: Dict[str, int]) -> int:
    m, o = ins.mnemonic, ins.operands
    ctx = f"line {ins.line_no} ({m})"
    expected = {
        "lui": 2, "addi": 3, "andi": 3, "xori": 3,
        "add": 3, "sub": 3, "and": 3, "xor": 3,
        "lw": 2, "sw": 2, "beq": 3, "bne": 3, "bltu": 3, "jal": 2,
    }[m]
    if len(o) != expected:
        raise AssemblerError(f"{ctx}: expected {expected} operands, received {len(o)}")

    if m == "lui":
        rd = parse_reg(o[0], ctx)
        return enc_u(rd, parse_number(o[1], ctx), ctx)
    if m in {"addi", "andi", "xori"}:
        rd = parse_reg(o[0], ctx); rs1 = parse_reg(o[1], ctx); imm = parse_number(o[2], ctx)
        funct3 = {"addi": 0, "xori": 4, "andi": 7}[m]
        return enc_i(0x13, rd, funct3, rs1, imm, ctx)
    if m in {"add", "sub", "and", "xor"}:
        rd = parse_reg(o[0], ctx); rs1 = parse_reg(o[1], ctx); rs2 = parse_reg(o[2], ctx)
        funct3 = {"add": 0, "sub": 0, "xor": 4, "and": 7}[m]
        funct7 = 0x20 if m == "sub" else 0
        return enc_r(rd, rs1, rs2, funct3, funct7)
    if m in {"lw", "sw"}:
        mem = MEM_RE.fullmatch(o[1] if m == "lw" else o[1])
        if m == "lw":
            rd = parse_reg(o[0], ctx)
            if not mem:
                raise AssemblerError(f"{ctx}: expected offset(xN), got {o[1]!r}")
            imm = parse_number(mem.group(1), ctx); rs1 = parse_reg(mem.group(2), ctx)
            return enc_i(0x03, rd, 2, rs1, imm, ctx)
        rs2 = parse_reg(o[0], ctx)
        if not mem:
            raise AssemblerError(f"{ctx}: expected offset(xN), got {o[1]!r}")
        imm = parse_number(mem.group(1), ctx); rs1 = parse_reg(mem.group(2), ctx)
        return enc_s(rs2, rs1, imm, 2, ctx)
    if m in {"beq", "bne", "bltu"}:
        rs1 = parse_reg(o[0], ctx); rs2 = parse_reg(o[1], ctx)
        offset = resolve_target(o[2], ins.pc, labels, ctx)
        funct3 = {"beq": 0, "bne": 1, "bltu": 6}[m]
        return enc_b(rs1, rs2, offset, funct3, ctx)
    if m == "jal":
        rd = parse_reg(o[0], ctx)
        offset = resolve_target(o[1], ins.pc, labels, ctx)
        return enc_j(rd, offset, ctx)
    raise AssemblerError(f"{ctx}: no encoder implemented")


def assemble_text(source: str) -> Tuple[List[int], Dict[str, int]]:
    instructions, labels = parse_source(source)
    words: List[int] = []
    for ins in instructions:
        try:
            words.append(encode_instruction(ins, labels))
        except AssemblerError as exc:
            raise AssemblerError(f"{exc}\n  source: {ins.source.strip()}") from exc
    return words, labels


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="input Assembly source (e.g. sw/game.s)")
    parser.add_argument("-o", "--output", type=Path, required=True, help="output hex path")
    parser.add_argument("--symbols", type=Path, help="optionally write label address table")
    args = parser.parse_args(argv)
    try:
        source_text = args.source.read_text(encoding="utf-8")
        words, labels = assemble_text(source_text)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text("".join(f"{word:08x}\n" for word in words), encoding="ascii")
        if args.symbols:
            args.symbols.parent.mkdir(parents=True, exist_ok=True)
            args.symbols.write_text("".join(f"0x{address:08x} {name}\n" for name, address in sorted(labels.items(), key=lambda item: item[1])), encoding="utf-8")
        print(f"Assembled {args.source}: {len(words)} words -> {args.output}")
        return 0
    except (OSError, AssemblerError) as exc:
        print(f"assembler: error: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
