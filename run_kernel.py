"""Usage:  python run_kernel.py <vecadd|gradient|circle|checker> [--lanes N] [--vcd]"""
import argparse, pathlib
from tinygpu.assembler import assemble
from tinygpu.runner import run_gpu
from tinygpu.refmodel import run_ref
from tinygpu.image import write_png

ROOT = pathlib.Path(__file__).parent
IMG = {"gradient", "circle", "checker"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kernel")
    ap.add_argument("--lanes", type=int, default=8)
    ap.add_argument("--vcd", action="store_true", help="dump out/<kernel>.vcd for GTKWave/Surfer")
    a = ap.parse_args()

    prog = assemble((ROOT / "kernels" / f"{a.kernel}.s").read_text())
    out = ROOT / "out"; out.mkdir(exist_ok=True)

    if a.kernel == "vecadd":
        n = 16
        mem = list(range(n)) + list(range(100, 100 + n)) + [0] * n   # A, B, C
    else:
        n, mem = 32 * 32, []

    dmem, st = run_gpu(prog, mem, n, lanes=a.lanes,
                       vcd=str(out / f"{a.kernel}.vcd") if a.vcd else None)
    ok = dmem == run_ref(prog, mem + [0] * (2048 - len(mem)), n)
    print(f"{a.kernel}: {st}")
    print("matches reference model:", "YES" if ok else "NO  <-- BUG")

    if a.kernel == "vecadd":
        print("C =", dmem[32:48])
    else:
        p = out / f"{a.kernel}.png"
        write_png(p, dmem[:n], 32, 32)
        print("wrote", p)

if __name__ == "__main__":
    main()
