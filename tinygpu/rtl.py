"""Tiny SIMT GPU core in Amaranth HDL.

One core, `lanes` lanes in lockstep, one shared instruction stream.
Threads are dispatched in blocks of `lanes`: block b, lane l -> tid = b*lanes + l.
Multi-cycle FSM:  FETCH -> EXEC -> (MEM x lanes for ld/st) -> FETCH ...
The data memory has ONE port, so ld/st are serialized across lanes
(this is what makes memory-bound kernels visibly slower in cycle counts).
"""
from amaranth.hdl import Elaboratable, Module, Signal, Array
from .isa import OPS, NREGS, WORD


class TinyGPU(Elaboratable):
    def __init__(self, program, dmem_init, lanes=8, blocks=1, dmem_depth=2048):
        assert len(dmem_init) <= dmem_depth
        self.L, self.blocks, self.depth = lanes, blocks, dmem_depth
        self.imem = Array(Signal(32, init=w, name=f"imem{i}") for i, w in enumerate(program))
        init = list(dmem_init) + [0] * (dmem_depth - len(dmem_init))
        self.dmem = Array(Signal(WORD, init=v, name=f"dmem{i}") for i, v in enumerate(init))
        self.regs = Array(Signal(WORD, name=f"r{l}_{r}")
                          for l in range(lanes) for r in range(NREGS))
        self.done = Signal()
        self.cycles = Signal(32)      # total cycles until done
        self.instrs = Signal(32)      # instructions issued (summed over blocks)
        self.mem_cycles = Signal(32)  # cycles spent in the serialized MEM stage

    def elaborate(self, platform):
        m = Module()
        L, R = self.L, NREGS
        pc = Signal(16)
        block = Signal(16)
        lane = Signal(range(L))
        instr = Signal(32)
        op, rd, ra, rb, imm = instr[25:30], instr[22:25], instr[19:22], instr[16:19], instr[0:16]

        A = [Signal(WORD, name=f"A{l}") for l in range(L)]
        B = [Signal(WORD, name=f"B{l}") for l in range(L)]
        for l in range(L):
            m.d.comb += [A[l].eq(self.regs[ra + l * R]), B[l].eq(self.regs[rb + l * R])]

        def alu(l):
            a, b = A[l], B[l]
            return {
                "ldi": imm, "tid": (block * L + l)[:WORD],
                "add": a + b, "sub": a - b, "mul": a * b,
                "and": a & b, "or": a | b, "xor": a ^ b,
                "shl": a << b[:4], "shr": a >> b[:4],
                "slt": a.as_signed() < b.as_signed(),
                "addi": a + imm,
            }

        # single memory port, serving one lane per cycle
        maddr = Signal(WORD)
        mdata = Signal(WORD)
        m.d.comb += [maddr.eq(self.regs[ra + lane * R] + imm),
                     mdata.eq(self.regs[rb + lane * R])]

        with m.If(~self.done):
            m.d.sync += self.cycles.eq(self.cycles + 1)

        with m.FSM():
            with m.State("FETCH"):
                m.d.sync += instr.eq(self.imem[pc])
                m.next = "EXEC"

            with m.State("EXEC"):
                m.d.sync += self.instrs.eq(self.instrs + 1)
                with m.Switch(op):
                    for name in ("ldi", "tid", "add", "sub", "mul", "and", "or",
                                 "xor", "shl", "shr", "slt", "addi"):
                        with m.Case(OPS[name]):
                            for l in range(L):
                                m.d.sync += self.regs[rd + l * R].eq(alu(l)[name])
                            m.d.sync += pc.eq(pc + 1)
                            m.next = "FETCH"
                    with m.Case(OPS["ld"], OPS["st"]):
                        m.d.sync += lane.eq(0)
                        m.next = "MEM"
                    with m.Case(OPS["halt"]):
                        m.d.sync += pc.eq(0)
                        with m.If(block == self.blocks - 1):
                            m.next = "DONE"
                        with m.Else():
                            m.d.sync += block.eq(block + 1)
                            m.next = "FETCH"
                    with m.Default():  # nop / illegal
                        m.d.sync += pc.eq(pc + 1)
                        m.next = "FETCH"

            with m.State("MEM"):
                m.d.sync += self.mem_cycles.eq(self.mem_cycles + 1)
                with m.If(op == OPS["ld"]):
                    with m.If(maddr < self.depth):
                        m.d.sync += self.regs[rd + lane * R].eq(self.dmem[maddr])
                with m.Else():
                    with m.If(maddr < self.depth):
                        m.d.sync += self.dmem[maddr].eq(mdata)
                with m.If(lane == L - 1):
                    m.d.sync += pc.eq(pc + 1)
                    m.next = "FETCH"
                with m.Else():
                    m.d.sync += lane.eq(lane + 1)

            with m.State("DONE"):
                m.d.comb += self.done.eq(1)
        return m
