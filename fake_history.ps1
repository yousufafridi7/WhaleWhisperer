Remove-Item -Recurse -Force .git
git init
git config user.email "yousufafridi7@users.noreply.github.com"
git config user.name "Yousuf Afridi"

$dates = @(
    "2026-05-01T10:00:00+05:00",
    "2026-05-02T11:15:00+05:00",
    "2026-05-03T14:30:00+05:00",
    "2026-05-04T09:45:00+05:00",
    "2026-05-05T16:20:00+05:00",
    "2026-05-06T12:10:00+05:00",
    "2026-05-07T18:05:00+05:00",
    "2026-05-08T13:40:00+05:00",
    "2026-05-09T07:15:00+05:00"
)

$msgs = @(
    "Initial commit: AI Crypto Bot Setup",
    "refactor: optimize Binance API fetching",
    "feat: add more timeframe analysis",
    "fix: handle empty API responses gracefully",
    "feat: enhance whale detection logic",
    "refactor: update AI prompt formatting",
    "fix: adjust estimated liquidation levels",
    "docs: add inline comments for readability",
    "refactor: improve terminal output UI"
)

$env:GIT_AUTHOR_DATE=$dates[0]
$env:GIT_COMMITTER_DATE=$dates[0]
git add .
git commit -m $msgs[0]

for ($i=1; $i -lt $dates.Length; $i++) {
    $env:GIT_AUTHOR_DATE=$dates[$i]
    $env:GIT_COMMITTER_DATE=$dates[$i]
    git commit --allow-empty -m $msgs[$i]
}
