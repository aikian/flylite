"""Live progress bar for Phase D (reads phaseD_log.txt written by run_phaseD.ps1).

usage: python phaseD_progress.py          (refreshes every 2 s; Ctrl+C to quit)
       python phaseD_progress.py --once   (print one snapshot and exit)
"""
import json, os, re, sys, time, ctypes
from datetime import datetime, timedelta
from pathlib import Path

LOG = Path(__file__).resolve().parent / "phaseD_log.txt"

# planned grid, in the exact order run_flylite.py executes it (ref first, then for k: for method: for seed)
BLOCKS = [
    dict(task="sugar",  noise=0.0, methods="randm", label="sugar  σ=0    randm k3,5 seed3,4  trial 3 ",
         items=[("randm", 3, 3), ("randm", 3, 4), ("randm", 5, 3), ("randm", 5, 4)], est=150),
    dict(task="bitter", noise=3.5, methods="mag",   label="bitter σ=3.5  ref + mag k2,5,10,31 trial 10",
         items=[("ref", 0, 0), ("mag", 2, 0), ("mag", 5, 0), ("mag", 10, 0), ("mag", 31, 0)], est=1200),
    dict(task="sugar",  noise=3.5, methods="mag",   label="sugar  σ=3.5  mag k5              trial 10",
         items=[("mag", 5, 0)], est=600),
    dict(task="sugar",  noise=3.5, methods="rand",  label="sugar  σ=3.5  rand k1,3 seed3,4   trial 10",
         items=[("rand", 1, 3), ("rand", 1, 4), ("rand", 3, 3), ("rand", 3, 4)], est=600),
]
LOAD_S = 30  # parquet + graph load before the first variant of a block

RE_JOB = re.compile(r">>> run_flylite\.py --tasks (\w+)\s+--noise ([\d.]+)\s+--methods (\w+).*\[(\d\d):(\d\d)\]")
RE_EXIT = re.compile(r"<<< exit (-?\d+)")


RE_REF = re.compile(r">>> reference\s+task=(\w+) noise=([\d.]+)")


def _infer_start(st, i):
    """Block start when the PowerShell marker is missing: previous block's start + load + its measured wall time."""
    if i == 0 or st["blocks"][i - 1]["started"] is None:
        return datetime.now()
    prev = st["blocks"][i - 1]
    return prev["started"] + timedelta(seconds=LOAD_S + sum(r.get("wall_s", 0) for _, r in prev["done"]) + 5)


def _begin(st, i):
    if st["blocks"][i]["started"] is None:
        st["blocks"][i]["started"] = _infer_start(st, i)
    return i


def parse():
    st = dict(blocks=[dict(started=None, done=[], exit=None) for _ in BLOCKS], finished=False, errors=[], started=None)
    if not LOG.exists():
        return st
    cur = None
    for line in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("=== Phase D start"):
            st["started"] = line.split("start")[-1].strip(" =")
            continue
        m = RE_JOB.search(line)
        if m:  # PowerShell marker (may be missing: the runner's own lines below also open a block)
            task, noise, meth, hh, mm = m.group(1), float(m.group(2)), m.group(3), int(m.group(4)), int(m.group(5))
            for i, b in enumerate(BLOCKS):
                if (b["task"], b["noise"], b["methods"]) == (task, noise, meth) and st["blocks"][i]["started"] is None:
                    cur = i
                    t = datetime.now().replace(hour=hh, minute=mm, second=0, microsecond=0)
                    if t > datetime.now() + timedelta(minutes=1):
                        t -= timedelta(days=1)  # block started before midnight
                    st["blocks"][i]["started"] = t
                    break
            continue
        m = RE_REF.search(line)
        if m:  # runner computes a fresh reference: first thing in a block with a new results dir
            task, noise = m.group(1), float(m.group(2))
            for i, b in enumerate(BLOCKS):
                if (b["task"], b["noise"]) == (task, noise) and st["blocks"][i]["exit"] is None and i != cur:
                    cur = _begin(st, i); break
            continue
        if line.startswith("{"):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = ("ref", 0, 0) if r.get("k") == 0 else (r.get("method"), r.get("k"), r.get("seed"))
            # attach to the current block if it fits, else to the first unfinished block that planned this row
            fits = lambda i: (BLOCKS[i]["task"], BLOCKS[i]["noise"]) == (r.get("task"), r.get("noise")) and key in BLOCKS[i]["items"]
            if cur is None or not fits(cur):
                cand = [i for i in range(len(BLOCKS)) if fits(i) and st["blocks"][i]["exit"] is None
                        and key not in [k for k, _ in st["blocks"][i]["done"]]]
                if not cand:
                    continue
                cur = _begin(st, cand[0])
            st["blocks"][cur]["done"].append((key, r))
            continue
        if line.startswith("=== done ===") and cur is not None:  # runner finished a block
            if st["blocks"][cur]["exit"] is None:
                st["blocks"][cur]["exit"] = 0
            continue
        m = RE_EXIT.search(line)
        if m and cur is not None:
            st["blocks"][cur]["exit"] = int(m.group(1))
            continue
        if line.startswith("=== Phase D done"):
            st["finished"] = True
        if "Traceback" in line or "MemoryError" in line or "Error:" in line:
            st["errors"].append(line[:110])
    return st


def bar(frac, width=24):
    n = int(round(max(0.0, min(1.0, frac)) * width))
    return "█" * n + "░" * (width - n)


def hms(sec):
    sec = max(0, int(sec))
    return f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}" if sec >= 3600 else f"{sec // 60:02d}:{sec % 60:02d}"


def metric_str(key, r):
    if key[0] == "ref":
        return "reference"
    if "sugar100_bitter100__readout" in r:  # bitter rows (log prints ratio only) -> SI unavailable here
        return f"sugar {r.get('sugar100__readout_ratio', float('nan')):.2f}"
    return f"readout {r.get('sugar100__readout_ratio', float('nan')):.2f}  corr {r.get('sugar100__pearson_union', float('nan')):.2f}"


def render(st):
    now = datetime.now()
    lines, total_est, total_done_s, remaining_s = [], 0.0, 0.0, 0.0
    n_items = sum(len(b["items"]) for b in BLOCKS); n_done = 0
    recent = []
    for i, (b, s) in enumerate(zip(BLOCKS, st["blocks"])):
        done_keys = [k for k, _ in s["done"]]
        walls = [r.get("wall_s", 0) for _, r in s["done"] if r.get("wall_s")]
        est = sum(walls) / len(walls) if walls else b["est"]  # adapt to measured speed once one item is in
        nd = sum(1 for it in b["items"] if it in done_keys); n_done += nd
        remaining = len(b["items"]) - nd
        # current item: the first planned one not done, if the block has started and not exited
        cur_txt, cur_elapsed = "", 0.0
        if s["started"] is not None and s["exit"] is None and remaining > 0:
            cur = next(it for it in b["items"] if it not in done_keys)
            start = s["started"] + timedelta(seconds=LOAD_S + sum(walls))
            cur_elapsed = max(0.0, (now - start).total_seconds())
            name = "reference (k=0)" if cur[0] == "ref" else f"{cur[0]} k={cur[1]}" + (f" seed={cur[2]}" if cur[0] in ("rand", "randm") else "")
            cur_txt = f"  ▶ {name}  {hms(cur_elapsed)} / ~{hms(est)}"
        block_rem = max(0.0, remaining * est - cur_elapsed)
        remaining_s += block_rem; total_est += len(b["items"]) * est
        frac = (nd + min(cur_elapsed / est, 0.97 if remaining else 0)) / len(b["items"])
        state = "✔ 완료" if remaining == 0 else ("✖ exit %d" % s["exit"] if s["exit"] not in (None, 0) else ("실행 중" if s["started"] else "대기"))
        lines.append(f" {i+1}. {b['label']}  {bar(frac, 20)} {nd}/{len(b['items'])}  {state}{cur_txt}")
        for k, r in s["done"]:
            if k in b["items"]:
                nm = "ref" if k[0] == "ref" else f"{k[0]} k={k[1]}" + (f" s{k[2]}" if k[0] in ("rand", "randm") else "")
                recent.append(f"{b['task']} σ={b['noise']:g} {nm}: {metric_str(k, r)}  ({r.get('wall_s', 0)} s)")
    done_s = total_est - remaining_s
    overall = done_s / total_est if total_est else 0
    eta = now + timedelta(seconds=remaining_s)
    head = [f" Phase D  {bar(overall, 36)} {overall*100:5.1f}%   {n_done}/{n_items} 변형",
            f" 시작 {st['started'] or '-'}   경과 {hms((now - st['blocks'][0]['started']).total_seconds()) if st['blocks'][0]['started'] else '-'}"
            f"   남은 시간 ≈ {hms(remaining_s)}   완료 예정 {eta.strftime('%H:%M')}" if not st["finished"] else " ✔ Phase D 전체 완료"]
    out = ["", *head, ""] + lines + [""]
    if recent:
        out += [" 최근 결과:"] + [f"   {x}" for x in recent[-8:]]
    if st["errors"]:
        out += ["", " !! 로그에 에러:"] + [f"   {e}" for e in st["errors"][-3:]]
    out += ["", f" {now.strftime('%H:%M:%S')}  (2초마다 갱신, Ctrl+C 종료)  로그: {LOG}"]
    return "\n".join(out)


def main():
    if os.name == "nt":
        ctypes.windll.kernel32.SetConsoleOutputCP(65000 + 1)  # UTF-8 so bars/Korean render
        os.system("")  # enable ANSI escapes in conhost
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if "--once" in sys.argv:
        print(render(parse())); return
    try:
        while True:
            st = parse()
            sys.stdout.write("\x1b[H\x1b[J" + render(st) + "\n"); sys.stdout.flush()
            if st["finished"]:
                break
            time.sleep(2)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
