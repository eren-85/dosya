<# =======================================================================
 Sigma Analyst – PowerShell Shortcuts (sigma_cli.ps1)
 -----------------------------------------------------------------------
 Dot-source once per session:
   PS> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force
   PS> Unblock-File .\sigma_cli.ps1
   PS> . .\sigma_cli.ps1

 Quick start:
   PS> SA-UseDocker -On            # default: ON
   PS> SA-Up                       # start docker compose services
   PS> SA-Download -Symbols "BTCUSDT,ETHUSDT" -Interval 1h -Market futures -AllTime -Parquet
   PS> SA-Sync     -Symbols "BTCUSDT,ETHUSDT" -Interval 4h -Market spot -Parquet
   PS> SA-Oneshot  -Symbols "BTCUSDT,ETHUSDT" -Timeframes "1h,4h,1d"
   PS> SA-Ls -Limit 10 | SA-Result
   PS> SA-Flower

 Notes:
 - Docker mode runs:  docker compose exec backend python -m backend.cli ...
 - Local mode runs:   python -m backend.cli ...
 - Allowed intervals (direct from exchange): 5m,15m,30m,1h,4h,1d,1w,1M
   (Intermediate like 2h,3h,12h,3d are derived downstream from stored data.)
======================================================================= #>

# ----------------------------
# Global / Script preferences
# ----------------------------
$script:SA_DOCKER = $true

function SA-UseDocker {
  [CmdletBinding()]
  param(
    [switch]$On,
    [switch]$Off
  )
  if ($On -and $Off) { throw "Use either -On or -Off." }
  if ($On)  { $script:SA_DOCKER = $true  }
  if ($Off) { $script:SA_DOCKER = $false }
  "Docker mode: {0}" -f ($(if ($script:SA_DOCKER) {'ON'} else {'OFF'}))
}

# ----------------------------
# Internals
# ----------------------------
function _SA-BuildCliArgs {
  param([string[]]$Parts)
  # Return array suitable for PowerShell's "&" invocation
  return ,$Parts
}

function _SA-InvokeCli {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$true)][string[]]$CliArgs,
    [switch]$Quiet
  )
  if ($script:SA_DOCKER) {
    $cmd = @("docker","compose","exec","backend","python","-m","backend.cli") + $CliArgs
  } else {
    $cmd = @("python","-m","backend.cli") + $CliArgs
  }
  if (-not $Quiet) { Write-Host ("`n> " + ($cmd -join ' ')) -ForegroundColor DarkGray }
  & $cmd
}

function _SA-ValidateComposeYml {
  if ($script:SA_DOCKER) {
    $yml = Join-Path -Path (Get-Location) -ChildPath "docker-compose.yml"
    if (-not (Test-Path $yml)) {
      Write-Warning "docker-compose.yml not found in $(Get-Location). Make sure you're in the project root."
    }
  }
}

# ----------------------------
# Service orchestration
# ----------------------------
function SA-Up {
  [CmdletBinding()]
  param(
    [string[]]$Services # optional: specify a subset like @('backend','redis','celery_worker')
  )
  _SA-ValidateComposeYml
  if (-not $script:SA_DOCKER) {
    Write-Host "Local mode: nothing to start. Ensure your venv + backend is running." -ForegroundColor Yellow
    return
  }
  $base = @("docker","compose","up","-d")
  if ($Services) { $base += $Services }
  & $base | Out-Host
}

function SA-Down {
  [CmdletBinding()]
  param()
  if (-not $script:SA_DOCKER) { return }
  & docker compose down | Out-Host
}

# ----------------------------
# High level helpers
# ----------------------------
$allowedIntervals = '5m','15m','30m','1h','4h','1d','1w','1M'
$allowedMarkets   = 'spot','futures'

function SA-Download {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$true)][string]$Symbols,
    [Parameter(Mandatory=$true)][ValidateSet('5m','15m','30m','1h','4h','1d','1w','1M')][string]$Interval,
    [Parameter(Mandatory=$true)][ValidateSet('spot','futures')][string]$Market,
    [switch]$AllTime,
    [switch]$Parquet
  )
  $args = @("download","-s",$Symbols,"-i",$Interval,"-m",$Market)
  if ($AllTime) { $args += "--all-time" }
  if ($Parquet) { $args += "--parquet" }
  _SA-InvokeCli -CliArgs $args
}

function SA-Sync {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$true)][string]$Symbols,
    [Parameter(Mandatory=$true)][ValidateSet('5m','15m','30m','1h','4h','1d','1w','1M')][string]$Interval,
    [Parameter(Mandatory=$true)][ValidateSet('spot','futures')][string]$Market,
    [switch]$Parquet
  )
  $args = @("sync","-s",$Symbols,"-i",$Interval,"-m",$Market)
  if ($Parquet) { $args += "--parquet" }
  _SA-InvokeCli -CliArgs $args
}

function SA-Train {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$true)][string]$Symbols,
    [Parameter(Mandatory=$true)][string]$Timeframes
  )
  $args = @("train","-s",$Symbols,"-t",$Timeframes)
  _SA-InvokeCli -CliArgs $args
}

function SA-Analyze {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$true)][string]$Symbols,
    [Parameter(Mandatory=$true)][string]$Timeframes,
    [switch]$Json
  )
  $args = @("analyze","-s",$Symbols,"-t",$Timeframes)
  if ($Json) { $args += "--json" }
  _SA-InvokeCli -CliArgs $args
}

function SA-Oneshot {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$true)][string]$Symbols,
    [Parameter(Mandatory=$true)][string]$Timeframes,
    [string]$CollectQueue = "market",
    [string]$DailyQueue   = "analysis",
    [int]$IntervalSec = 1,
    [int]$TimeoutSec  = 600
  )
  $args = @(
    "oneshot","-s",$Symbols,"-t",$Timeframes,
    "--collect-queue",$CollectQueue,
    "--daily-queue",$DailyQueue,
    "--interval",$IntervalSec,
    "--timeout",$TimeoutSec
  )
  _SA-InvokeCli -CliArgs $args
}

function SA-Ls {
  [CmdletBinding()]
  param([int]$Limit = 10)
  $args = @("ls","--limit",$Limit)
  _SA-InvokeCli -CliArgs $args
}

function SA-Result {
  [CmdletBinding(DefaultParameterSetName="Ids")]
  param(
    [Parameter(ParameterSetName="Ids", Position=0)][string]$Ids,
    [Parameter(ParameterSetName="FromPipe", ValueFromPipeline=$true)][string]$FromPipe
  )
  begin { $all = @() }
  process {
    if ($PSCmdlet.ParameterSetName -eq "FromPipe" -and $FromPipe) {
      $all += $FromPipe
    }
  }
  end {
    $joined = if ($Ids) { $Ids } else { ($all -replace '^celery-task-meta-','') -join ',' }
    if (-not $joined) { Write-Error "No IDs provided."; return }
    $args = @("result","--ids",$joined)
    _SA-InvokeCli -CliArgs $args
  }
}

function SA-Watch {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$true)][string]$Ids,
    [switch]$PrintResult
  )
  $args = @("watch","--ids",$Ids)
  if ($PrintResult) { $args += "--print-result" }
  _SA-InvokeCli -CliArgs $args
}

function SA-Flower {
  [CmdletBinding()]
  param([int]$Port = 5555)
  Start-Process -FilePath "http://localhost:$Port"
}

function SA-Help {
@"
Sigma Analyst – Available commands

  SA-UseDocker -On | -Off
  SA-Up [ -Services backend,redis,postgres,celery_worker,celery_beat,flower ]
  SA-Down
  SA-Download -Symbols "BTCUSDT,ETHUSDT" -Interval 1h -Market futures [-AllTime] [-Parquet]
  SA-Sync     -Symbols "BTCUSDT,ETHUSDT" -Interval 4h -Market spot [-Parquet]
  SA-Train    -Symbols "BTCUSDT" -Timeframes "1h,4h,1d"
  SA-Analyze  -Symbols "BTCUSDT" -Timeframes "1h,4h,1d" [-Json]
  SA-Oneshot  -Symbols "BTCUSDT,ETHUSDT" -Timeframes "1h,4h,1d" [-CollectQueue q] [-DailyQueue q] [-IntervalSec 1] [-TimeoutSec 600]
  SA-Ls [-Limit 10] | SA-Result
  SA-Result   -Ids "uuid1,uuid2"    (or pipe from SA-Ls)
  SA-Watch    -Ids "uuid" [-PrintResult]
  SA-Flower   [-Port 5555]

Intervals allowed: 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M
Markets: spot, futures
"@ | Out-Host
}

Write-Host "Sigma CLI loaded. Try: SA-UseDocker -On, SA-Up, SA-Download, SA-Sync, SA-Oneshot, SA-Ls, SA-Result, SA-Watch, SA-Flower" -ForegroundColor Cyan
