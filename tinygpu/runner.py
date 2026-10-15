from amaranth.sim import Simulator
from .rtl import TinyGPU


def run_gpu(program, dmem_init, n_threads, lanes=8, dmem_depth=2048,
            vcd=None, max_cycles=2_000_000):
    """Simulate the GPU until it halts. Returns (dmem, stats)."""
    if n_threads % lanes:
        raise ValueError("n_threads must be a multiple of lanes")
    dut = TinyGPU(program, dmem_init, lanes=lanes, blocks=n_threads // lanes,
                  dmem_depth=dmem_depth)
    sim = Simulator(dut)
    sim.add_clock(1e-6)
    out = {}

    async def tb(ctx):
        n = 0
        while not ctx.get(dut.done):
            await ctx.tick()
            n += 1
            if n > max_cycles:
                raise TimeoutError("GPU did not finish")
        out["dmem"] = [ctx.get(s) for s in dut.dmem]
        out["stats"] = dict(cycles=ctx.get(dut.cycles), instrs=ctx.get(dut.instrs),
                            mem_cycles=ctx.get(dut.mem_cycles), lanes=lanes,
                            threads=n_threads)

    sim.add_testbench(tb)
    if vcd:
        with sim.write_vcd(vcd):
            sim.run()
    else:
        sim.run()
    return out["dmem"], out["stats"]
