param([Parameter(Mandatory=$true)][string]$Checkout, [string]$Python = 'python')
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $Checkout
try {
    $expected = '6c3acba2f22d582cbe9102d9e9aea3f12b31b62d'
    if ((git rev-parse HEAD) -ne $expected) { throw 'Wrong audit commit' }
    if (git status --porcelain) { throw 'Checkout must be clean' }
    & $Python -c "import importlib.util; assert importlib.util.find_spec('moomoo') is None; from zoneinfo import ZoneInfo; ZoneInfo('America/New_York')"
    if ($LASTEXITCODE -ne 0) { throw 'Use an SDK-free environment with tzdata==2025.2' }
    foreach ($script in @('research/feed_contract/run_checks.py', 'offline_checks.py', 'research/reconciliation/run_checks.py', 'research/reconciliation/verify_evidence.py')) {
        & $Python -B $script
        if ($LASTEXITCODE -ne 0) { throw "Failed: $script" }
    }
    & $Python -B -c "import ast, pathlib; files=list(pathlib.Path('.').rglob('*.py')); [ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p)) for p in files]; print('Parsed', len(files), 'Python sources')"
    if ($LASTEXITCODE -ne 0) { throw 'Syntax check failed' }
    if (git status --porcelain) { throw 'Checkout changed during verification' }
} finally { Pop-Location }
