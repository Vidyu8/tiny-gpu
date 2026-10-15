"""Golden model: executes the program one thread at a time in plain Python."""
from .isa import decode, OPNAME

M = 0xFFFF

def _s(x):
    return x - 0x10000 if x & 0x8000 else x

def run_ref(program, dmem, n_threads, max_steps=10_000):
    dmem = list(dmem)
    for t in range(n_threads):
        r = [0] * 8
        pc = 0
        for _ in range(max_steps):
            op, rd, ra, rb, imm = decode(program[pc])
            name = OPNAME[op]
            a, b = r[ra], r[rb]
            if name == "halt":
                break
            elif name == "ldi":  r[rd] = imm
            elif name == "tid":  r[rd] = t & M
            elif name == "add":  r[rd] = (a + b) & M
            elif name == "sub":  r[rd] = (a - b) & M
            elif name == "mul":  r[rd] = (a * b) & M
            elif name == "and":  r[rd] = a & b
            elif name == "or":   r[rd] = a | b
            elif name == "xor":  r[rd] = a ^ b
            elif name == "shl":  r[rd] = (a << (b & 15)) & M
            elif name == "shr":  r[rd] = a >> (b & 15)
            elif name == "slt":  r[rd] = int(_s(a) < _s(b))
            elif name == "addi": r[rd] = (a + imm) & M
            elif name == "ld":
                addr = (a + imm) & M
                if addr < len(dmem):
                    r[rd] = dmem[addr]
            elif name == "st":
                addr = (a + imm) & M
                if addr < len(dmem):
                    dmem[addr] = b
            pc += 1
        else:
            raise RuntimeError(f"thread {t} did not halt")
    return dmem
