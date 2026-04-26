$env:PGPASSWORD = "postgres123"
$pgRoot = "E:\work\QuantaMind\services\PostgreSQL"
$appDir = "$pgRoot\app"
$dataDir = "$pgRoot\data"
$logFile = "$pgRoot\postgres.log"

& "$appDir\bin\pg_ctl.exe" -D $dataDir -l $logFile start
