@echo off
chcp 65001 > nul
mode con cols=200 lines=50
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p --default-character-set=utf8mb4