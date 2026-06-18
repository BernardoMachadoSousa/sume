@echo off 
cd /d "D:\Bernardo Jonas\sume" 
call venv\Scripts\activate 
echo Salve os arquivos no VS Code (Ctrl+K, S) antes de continuar. 
pause 
git add . 
set /p msg="Mensagem: " 
git commit -m "%%msg%%" 
git push 
pause 
