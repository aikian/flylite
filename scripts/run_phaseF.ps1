# Phase F (2026-09-19): robustness of the sugar cliff to connectome version and synaptic gain.
#   results/phaseF_783 : FlyWire v783 connectome, w_syn x1.0   mag k=5,10,20  (sugar, sigma=0, 3 trials)
#   results/phaseF_w08 : v630, w_syn x0.8                        mag k=5,10,20
#   results/phaseF_w12 : v630, w_syn x1.2                        mag k=5,10,20
# Each block re-simulates its own full-model reference. Resumable: re-run to continue.
Set-Location C:\Users\donggyu\flylite
$env:PYTHONIOENCODING = "utf-8"; $env:PYTHONUNBUFFERED = "1"
Add-Type -Namespace Win32 -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
[void][Win32.Power]::SetThreadExecutionState(0x80000000 -bor 0x00000001)
$log = "phaseF_log.txt"
cmd /c "echo === Phase F start $(Get-Date -Format 'yyyy-MM-dd HH:mm') === >> $log"
$jobs = @(
  "--tasks sugar --noise 0 --methods mag --ks 5,10,20 --n-run 3 --connectome 783 --w-syn-scale 1.0 --out results/phaseF_783",
  "--tasks sugar --noise 0 --methods mag --ks 5,10,20 --n-run 3 --connectome 630 --w-syn-scale 0.8 --out results/phaseF_w08",
  "--tasks sugar --noise 0 --methods mag --ks 5,10,20 --n-run 3 --connectome 630 --w-syn-scale 1.2 --out results/phaseF_w12"
)
foreach ($j in $jobs) {
  cmd /c "echo ^>^>^> run_flylite.py $j   [$(Get-Date -Format 'HH:mm')] >> $log"
  cmd /c ".venv\Scripts\python.exe run_flylite.py $j >> $log 2>&1"
  cmd /c "echo ^<^<^< exit $LASTEXITCODE   [$(Get-Date -Format 'HH:mm')] >> $log"
}
cmd /c "echo === Phase F done $(Get-Date -Format 'yyyy-MM-dd HH:mm') === >> $log"
[void][Win32.Power]::SetThreadExecutionState(0x80000000)
