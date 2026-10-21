@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo Pochoco Reflex - Build para Windows
echo Debe ejecutarse desde la consola de OSS CAD Suite (start.bat)
echo ============================================================
echo.

where python3 >nul 2>&1
if errorlevel 1 (
  echo ERROR: no encuentro python3.
  echo Abre primero la consola de OSS CAD Suite con start.bat.
  goto :fail
)
where yosys >nul 2>&1
if errorlevel 1 (
  echo ERROR: no encuentro yosys. Abre la consola de OSS CAD Suite.
  goto :fail
)
where nextpnr-ice40 >nul 2>&1
if errorlevel 1 (
  echo ERROR: no encuentro nextpnr-ice40. Abre la consola de OSS CAD Suite.
  goto :fail
)
where icepack >nul 2>&1
if errorlevel 1 (
  echo ERROR: no encuentro icepack. Abre la consola de OSS CAD Suite.
  goto :fail
)

echo [1/4] Generando sw\game.hex con el assembler propio...
python3 tools\assembler.py sw\game.s -o sw\game.hex --symbols sw\game.symbols
if errorlevel 1 goto :fail

echo.
echo [2/4] Ejecutando pruebas del assembler...
python3 -m unittest discover -s tests -v
if errorlevel 1 goto :fail

echo.
echo [3/4] Sintetizando game_top y generando game_top.json...
yosys -p "read_verilog rtl/espino_alu.v rtl/espino_controller.v rtl/espino_core.v rtl/espino_decoder.v rtl/espino_id_stage.v rtl/espino_if_stage.v rtl/espino_load_store_unit.v rtl/espino_register_file.v rtl/game_top.v rtl/pochoco_periph.v rtl/pochoco_ram.v rtl/pochoco_soc.v rtl/pochoco_spi_slave.v; synth_ice40 -top game_top -json game_top.json; stat"
if errorlevel 1 goto :fail

echo.
echo [4/4] Place and route, luego empaquetado del bitstream...
nextpnr-ice40 --hx1k --package vq100 --freq 25 --json game_top.json --pcf goboard.pcf --asc game_top.asc
if errorlevel 1 goto :fail
icepack game_top.asc game_top.bin
if errorlevel 1 goto :fail

echo.
echo BUILD COMPLETADO.
echo Se genero: game_top.bin
 echo Para programar la placa, revisa las instrucciones y ejecuta program_windows.bat.
echo La compilacion exitosa no reemplaza la prueba funcional en la Go Board.
goto :done

:fail
echo.
echo BUILD FALLIDO. Revisa el primer mensaje ERROR anterior; no programes la placa aun.
exit /b 1

:done
pause
exit /b 0
