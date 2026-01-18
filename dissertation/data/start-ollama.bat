@echo off
REM Start Ollama with CORS enabled for browser-based tools
set OLLAMA_ORIGINS=*
echo Starting Ollama with CORS enabled...
echo.
echo Models available:
"C:\Users\babaj\AppData\Local\Programs\Ollama\ollama.exe" list
echo.
echo Ollama is now ready for browser access.
echo Keep this window open while using RoleBox tools.
echo.
"C:\Users\babaj\AppData\Local\Programs\Ollama\ollama.exe" serve
