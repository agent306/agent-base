param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'agent_base.py') @Arguments
exit $LASTEXITCODE
