@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo Programar la memoria flash de la Nandland Go Board
echo ============================================================
if not exist game_top.bin (
  echo ERROR: no existe game_top.bin. Ejecuta build_windows.bat primero.
  exit /b 1
)
where iceprog >nul 2>&1
if errorlevel 1 (
  echo ERROR: no encuentro iceprog. Abre la consola de OSS CAD Suite con start.bat.
  exit /b 1
)
echo.
echo Confirma que:
echo   1. El bitstream game_top.bin se genero sin errores.
echo   2. La placa conectada es la Nandland Go Board con iCE40 HX1K VQ100.
echo   3. Instalaste el controlador USB necesario si Windows no detecta el programador.
echo.
echo Este paso escribe el bitstream en la memoria flash de la placa.
choice /C YN /N /M "Quieres continuar? [Y/N] "
if errorlevel 2 goto :cancel
iceprog game_top.bin
if errorlevel 1 (
  echo ERROR: iceprog no pudo programar la placa. Revisa USB/controlador y vuelve a intentar.
  exit /b 1
)
echo.
echo iceprog termino sin reportar error. Comprueba ahora el comportamiento fisico del juego.
pause
exit /b 0

:cancel
echo Programacion cancelada; no se ha ejecutado iceprog.
exit /b 0
