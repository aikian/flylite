"""Generate FlyLite_PhaseC_colab_v4.ipynb — the WHOLE Phase C on Colab (resumable, ~12-13 h, so expect one restart)."""
import json

cells = []
def md(s): cells.append({"cell_type": "markdown", "metadata": {}, "source": s})
def code(s): cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s})

md("""# FlyLite Phase C (v4, 전체) — Colab 실행용

**내용** (총 91개 변형, 약 12~13시간 → 무료 세션 한도에 걸려 한 번은 끊길 것)
1. bitter, groom: `act`(task-aware) + `shuf`(가중치 셔플 null) × σ{0, 3.5} × k{2,5,10,31} × seed 3
2. sugar: `shuf` × k{2,5,10,31} × seed 3
3. sugar: `randm`(시냅스 질량 맞춘 random null) × k{1,2,3,5,10} × seed 3

**사용법**
1. Drive `내 드라이브/flylite/` 에 **최신 run_flylite.py** (randm 포함) 와 task_ids.json
2. 런타임 → 런타임 유형 변경 → **CPU**
3. 런타임 → **모두 실행**, Drive 권한 허용
4. **끊기면 다시 "모두 실행"** — 끝난 조건은 자동으로 건너뜀. 몇 번 끊겨도 됨.

진행: 실행 셀에 분 단위로 찍히고 `flylite/results/phaseC/phaseC_log.txt` 에도 기록.
결과: `flylite/results/phaseC/summary.csv` (91행 + 기준행 6개가 되면 완료)""")

code("""from google.colab import drive
drive.mount('/content/drive')
import os
WORK = '/content/drive/MyDrive/flylite'
os.makedirs(WORK + '/results/phaseC', exist_ok=True)
print('work dir:', WORK)""")

code("""%%bash
cd /content
if [ ! -d Drosophila_brain_model ]; then
  git clone --depth 1 https://github.com/philshiu/Drosophila_brain_model
fi
pip install -q brian2 pyarrow joblib
python -c "import brian2; print('brian2', brian2.__version__)"
""")

code("""import shutil, os
for f in ['run_flylite.py', 'task_ids.json']:
    src = f'{WORK}/{f}'
    assert os.path.exists(src), f'{src} 없음 — Drive 의 flylite 폴더에 올려주세요'
    shutil.copy(src, '/content/' + f)
os.makedirs('/content/repos', exist_ok=True)
if not os.path.exists('/content/repos/Drosophila_brain_model'):
    os.symlink('/content/Drosophila_brain_model', '/content/repos/Drosophila_brain_model')
assert 'randm' in open('/content/run_flylite.py').read(), 'run_flylite.py 가 구버전입니다 (randm 없음) — 새 파일을 Drive 에 올려주세요'
print('runner ok')""")

code("""import os, pandas as pd
p = f'{WORK}/results/phaseC/summary.csv'
if os.path.exists(p):
    d = pd.read_csv(p); print('already done:', len(d), 'rows'); print(d.groupby(['task','noise','method']).size())
else:
    print('no results yet — fresh start')""")

code("""import subprocess, sys, time
log_path = f'{WORK}/results/phaseC/phaseC_log.txt'
OUT = f'{WORK}/results/phaseC'
RUNS = [
    ['--tasks', 'bitter,groom', '--noise', '0,3.5', '--methods', 'act,shuf', '--ks', '2,5,10,31', '--seeds', '0,1,2', '--n-run', '3'],
    ['--tasks', 'sugar',        '--noise', '0',     '--methods', 'shuf',     '--ks', '2,5,10,31', '--seeds', '0,1,2', '--n-run', '3'],
    ['--tasks', 'sugar',        '--noise', '0',     '--methods', 'randm',    '--ks', '1,2,3,5,10', '--seeds', '0,1,2', '--n-run', '3'],
]
t0 = time.time()
for i, args in enumerate(RUNS, 1):
    cmd = [sys.executable, '-u', '/content/run_flylite.py'] + args + ['--out', OUT]
    print(f'=== run {i}/{len(RUNS)}:', ' '.join(args), flush=True)
    with open(log_path, 'a') as log:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd='/content')
        for line in p.stdout:
            line = line.rstrip()
            if 'RuntimeWarning' in line or 'py.warnings' in line or line.strip().startswith('c /='):
                continue
            stamp = f'[{(time.time()-t0)/60:5.1f} min] '
            print(stamp + line, flush=True); log.write(stamp + line + '\\n'); log.flush()
        p.wait()
    print(f'=== run {i} exit code', p.returncode, flush=True)
print('ALL DONE')""")

code("""import pandas as pd
d = pd.read_csv(f'{WORK}/results/phaseC/summary.csv')
print(len(d), 'rows'); print(d.groupby(['task','noise','method']).size())""")

nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"},
      "colab": {"provenance": []}}, "nbformat": 4, "nbformat_minor": 0}
json.dump(nb, open("FlyLite_PhaseC_colab_v4.ipynb", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("wrote FlyLite_PhaseC_colab_v4.ipynb")
