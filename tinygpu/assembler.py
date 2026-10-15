import re
from .isa import OPS, encode

_REG = r"r([0-7])"
_MEM = rf"\[\s*{_REG}\s*(?:\+\s*(-?\d+))?\s*\]"

def _num(s):
    return int(s, 0)

def assemble(src: str) -> list[int]:
    prog = []
    for n, line in enumerate(src.splitlines(), 1):
        line = re.split(r"[;#]", line)[0].strip().lower()
        if not line:
            continue
        m = re.match(r"(\w+)\s*(.*)", line)
        mn, rest = m.group(1), m.group(2)
        if mn not in OPS:
            raise SyntaxError(f"line {n}: unknown op '{mn}'")
        op = OPS[mn]
        try:
            if mn in ("nop", "halt"):
                w = encode(op)
            elif mn == "tid":
                w = encode(op, rd=int(re.fullmatch(_REG, rest).group(1)))
            elif mn == "ldi":
                a = re.fullmatch(rf"{_REG}\s*,\s*(-?\w+)", rest)
                w = encode(op, rd=int(a.group(1)), imm=_num(a.group(2)))
            elif mn == "addi":
                a = re.fullmatch(rf"{_REG}\s*,\s*{_REG}\s*,\s*(-?\w+)", rest)
                w = encode(op, rd=int(a[1]), ra=int(a[2]), imm=_num(a[3]))
            elif mn == "ld":
                a = re.fullmatch(rf"{_REG}\s*,\s*{_MEM}", rest)
                w = encode(op, rd=int(a[1]), ra=int(a[2]), imm=int(a[3] or 0))
            elif mn == "st":
                a = re.fullmatch(rf"{_MEM}\s*,\s*{_REG}", rest)
                w = encode(op, ra=int(a[1]), imm=int(a[2] or 0), rb=int(a[3]))
            else:  # 3-register ALU
                a = re.fullmatch(rf"{_REG}\s*,\s*{_REG}\s*,\s*{_REG}", rest)
                w = encode(op, rd=int(a[1]), ra=int(a[2]), rb=int(a[3]))
        except (AttributeError, TypeError):
            raise SyntaxError(f"line {n}: bad operands for '{mn}': {rest!r}") from None
        prog.append(w)
    return prog
