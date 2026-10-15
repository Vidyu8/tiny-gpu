"""ISA definition shared by assembler, reference model and RTL.

32-bit instruction word (only 30 bits used):
  [29:25] op   [24:22] rd   [21:19] ra   [18:16] rb   [15:0] imm
8 registers per lane (r0..r7), 16-bit data path.
"""
WORD = 16
NREGS = 8

OPS = {
    "nop": 0, "halt": 1,
    "ldi": 2,    # rd = imm
    "tid": 3,    # rd = global thread id
    "add": 4, "sub": 5, "mul": 6,
    "and": 7, "or": 8, "xor": 9,
    "shl": 10, "shr": 11,   # shift amount = rb[3:0]
    "slt": 12,   # rd = (signed ra < signed rb)
    "addi": 13,  # rd = ra + imm
    "ld": 14,    # rd = mem[ra + imm]
    "st": 15,    # mem[ra + imm] = rb
}
OPNAME = {v: k for k, v in OPS.items()}

def encode(op, rd=0, ra=0, rb=0, imm=0):
    return (op << 25) | (rd << 22) | (ra << 19) | (rb << 16) | (imm & 0xFFFF)

def decode(w):
    return ((w >> 25) & 31, (w >> 22) & 7, (w >> 19) & 7, (w >> 16) & 7, w & 0xFFFF)
