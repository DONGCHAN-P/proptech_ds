param([int]$RenderPid)
Wait-Process -Id $RenderPid -ErrorAction SilentlyContinue
& node (Join-Path $PSScriptRoot 'finish.cjs')
exit $LASTEXITCODE
