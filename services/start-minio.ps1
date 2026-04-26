$cmd = 'set MINIO_ROOT_USER=minioadmin && set MINIO_ROOT_PASSWORD=minioadmin && "E:\work\QuantaMind\services\minio.exe" server "E:\work\QuantaMind\services\minio-data" --address :9000 --console-address :9001'
Start-Process -WindowStyle Hidden -FilePath "cmd.exe" -ArgumentList "/c $cmd" -WorkingDirectory "E:\work\QuantaMind\services"
