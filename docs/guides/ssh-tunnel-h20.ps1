$ErrorActionPreference = 'Continue'
$logFile = Join-Path $env:USERPROFILE '.ssh\ssh-tunnel-h20.log'
function Write-Log([string]$msg) {
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    "$ts  $msg" | Out-File -FilePath $logFile -Append -Encoding utf8
}
Write-Log "=== tunnel daemon started (PID $PID) ==="
while ($true) {
    Write-Log "connecting to h20-zq ..."
    & ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ConnectTimeout=10 -o TCPKeepAlive=yes -N -L 127.0.0.1:8081:gitlab.irootech.com:80 -D 127.0.0.1:1081 h20-zq
    Write-Log "ssh exited (code $LASTEXITCODE), retry in 60s"
    Start-Sleep -Seconds 60
}
