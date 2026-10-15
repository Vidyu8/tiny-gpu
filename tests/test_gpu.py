import pathlib, random, pytest
from tinygpu.assembler import assemble
from tinygpu.runner import run_gpu
from tinygpu.refmodel import run_ref
from tinygpu.isa import decode, OPS

K = pathlib.Path(__file__).parent.parent / "kernels"
DEPTH = 2048
pad = lambda m: m + [0] * (DEPTH - len(m))


def test_assembler_roundtrip():
    w = assemble("ld r2, [r1 + 16]\nst [r3 + 5], r4\nsub r1, r2, r3")[:3]
    assert decode(w[0]) == (OPS["ld"], 2, 1, 0, 16)
    assert decode(w[1]) == (OPS["st"], 0, 3, 4, 5)
    assert decode(w[2]) == (OPS["sub"], 1, 2, 3, 0)


def test_vecadd_exact():
    prog = assemble((K / "vecadd.s").read_text())
    mem = list(range(16)) + list(range(100, 116)) + [0] * 16
    dmem, _ = run_gpu(prog, mem, 16, lanes=8)
    assert dmem[32:48] == [i + 100 + i for i in range(16)]


@pytest.mark.parametrize("kernel", ["gradient", "circle", "checker"])
@pytest.mark.parametrize("lanes", [4, 16])
def test_image_kernels_match_reference(kernel, lanes):
    prog = assemble((K / f"{kernel}.s").read_text())
    dmem, _ = run_gpu(prog, [], 1024, lanes=lanes)
    assert dmem == run_ref(prog, pad([]), 1024)


def test_random_alu_programs_match_reference():
    """Fuzz: random straight-line ALU programs, RTL vs golden model (r1 = tid kept intact so stores never collide)."""
    rnd = random.Random(1234)
    ops = ["add", "sub", "mul", "and", "or", "xor", "shl", "shr", "slt"]
    for _ in range(8):
        src = ["tid r1"] + [f"ldi r{i}, {rnd.randint(0, 65535)}" for i in range(2, 8)]  # regs are not cleared between blocks
        for _ in range(12):
            src.append(f"{rnd.choice(ops)} r{rnd.randint(2,7)}, r{rnd.randint(1,7)}, r{rnd.randint(1,7)}")
        src += ["st [r1 + 0], r" + str(rnd.randint(1, 7)), "halt"]
        prog = assemble("\n".join(src))
        dmem, _ = run_gpu(prog, [], 16, lanes=8, dmem_depth=64)
        assert dmem == run_ref(prog, [0] * 64, 16), "\n".join(src)


def test_memory_port_is_serialized():
    prog = assemble((K / "vecadd.s").read_text())
    _, s8 = run_gpu(prog, [0] * 48, 16, lanes=8)
    # 3 mem instrs x 8 lanes x 2 blocks
    assert s8["mem_cycles"] == 3 * 8 * 2
