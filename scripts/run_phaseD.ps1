# Phase D (2026-09-18): seed/trial reinforcement for the key sigma=3.5 conditions + randm seeds 3,4.
# Each block appends to an existing results dir (resumable; finished variants are skipped) so the
# reference (k=0) and trial count stay consistent within that dir:
#   results/phaseC  : sugar sigma=0  randm k=3,5 seeds 3,4   (trial 3, Colab reference)        ~12 min
#   results/phaseD  : bitter sigma=3.5 mag k=2,5,10,31       (trial 10, fresh reference)       ~100 min
#   results/phaseA2 : sugar sigma=3.5 mag k=5, rand k=1,3 seeds 3,4 (trial 10, A2 reference)  ~50 min
# Re-run this script to resume after an interruption.
Set-Location C:\Users\donggyu\flylite
$env:PYTHONIOENCODING = "utf-8"; $env:PYTHONUNBUFFERED = "1"
# keep the system awake for the duration of this process only (display may still sleep); no power-plan change
Add-Type -Namespace Win32 -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
[void][Win32.Power]::SetThreadExecutionState(0x80000000 -bor 0x00000001)   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED

$log = "phaseD_log.txt"
Start-Transcript -Path "phaseD_transcript.txt" -Append | Out-Null
Add-Content $log "=== Phase D start $(Get-Date -Format 'yyyy-MM-dd HH:mm') ==="
$jobs = @(
  "--tasks sugar  --noise 0   --methods randm --ks 3,5       --seeds 3,4 --n-run 3  --out results/phaseC",
  "--tasks bitter --noise 3.5 --methods mag   --ks 2,5,10,31             --n-run 10 --out results/phaseD",
  "--tasks sugar  --noise 3.5 --methods mag   --ks 5                     --n-run 10 --out results/phaseA2",
  "--tasks sugar  --noise 3.5 --methods rand  --ks 1,3       --seeds 3,4 --n-run 10 --out results/phaseA2"
)
foreach ($j in $jobs) {
  # markers go through the same cmd redirection as the runner output (Add-Content silently lost the
  # 2026-09-18 23:57 markers, presumably a transient share-lock on the log)
  cmd /c "echo ^>^>^> run_flylite.py $j   [$(Get-Date -Format 'HH:mm')] >> $log"
  cmd /c ".venv\Scripts\python.exe run_flylite.py $j >> $log 2>&1"
  cmd /c "echo ^<^<^< exit $LASTEXITCODE   [$(Get-Date -Format 'HH:mm')] >> $log"
}
Add-Content $log "=== Phase D done $(Get-Date -Format 'yyyy-MM-dd HH:mm') ==="
[void][Win32.Power]::SetThreadExecutionState(0x80000000)
Stop-Transcript | Out-Null
