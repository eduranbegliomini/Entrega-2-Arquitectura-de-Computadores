@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

rem Uso:
rem   build.bat          ensambla sw\game.s, prueba, sintetiza y programa
rem   build.bat prueba   ensambla sw\prueba.s, sintetiza y programa
rem Ejecutar desde la consola de OSS CAD Suite.

set "SRC=sw\game.s"
if /i "%~1"=="prueba" set "SRC=sw\prueba.s"

echo === Ensamblando %SRC% -^> sw\game.hex
python tools\assembler.py "%SRC%" -o sw\game.hex --symbols sw\game.symbols || exit /b 1

if /i "%~1"=="prueba" goto skip_tests
echo === Pruebas del assembler
python -m unittest discover -s tests -v || exit /b 1
:skip_tests

set "READ="
for %%f in (rtl\*.v) do set "READ=!READ!read_verilog rtl/%%~nxf; "

echo === Sintesis Yosys (mapeo ABC LUT4 para evitar ABC9)
yosys -q -p "!READ!synth_ice40 -top game_top -run :map_luts; techmap -map +/ice40/latches_map.v; abc -dress -lut 4; ice40_wrapcarry -unwrap; techmap -map +/ice40/ff_map.v; clean; opt_lut -tech ice40; synth_ice40 -top game_top -run map_cells: -json game_top.json" || exit /b 1

echo === Place and route
nextpnr-ice40 --hx1k --package vq100 --freq 25 --json game_top.json --pcf goboard.pcf --asc game_top.asc || exit /b 1

echo === Crear bitstream
icepack game_top.asc game_top.bin || exit /b 1

echo === Programar la Go Board
iceprog game_top.bin || exit /b 1

echo === Listo. Se programo el archivo elegido en la placa.
