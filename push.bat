@echo off 
cd /d "D:\Bernardo Jonas\sume" 
call venv\Scripts\activate 
git add . 
set /p msg="Mensagem: " 
git commit -m "%%msg%%" 
git push 
pause 
