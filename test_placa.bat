@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
rem Diagnóstico sin procesador: comprueba el reloj, displays, botones, LEDs y programación.
rem Ejecutar desde la consola OSS CAD Suite.

echo === Sintesis del test_placa (ABC LUT4)
yosys -q -p "read_verilog test_placa/test_placa.v; synth_ice40 -top test_placa -run :map_luts; techmap -map +/ice40/latches_map.v; abc -dress -lut 4; ice40_wrapcarry -unwrap; techmap -map +/ice40/ff_map.v; clean; opt_lut -tech ice40; synth_ice40 -top test_placa -run map_cells: -json test_placa.json" || exit /b 1

echo === Place and route
nextpnr-ice40 --hx1k --package vq100 --freq 25 --json test_placa.json --pcf goboard.pcf --asc test_placa.asc || exit /b 1

echo === Crear bitstream
icepack test_placa.asc test_placa.bin || exit /b 1

echo === Programar la Go Board
iceprog test_placa.bin || exit /b 1

echo === Listo. LEDs deben reflejar botones; displays deben contar en hexadecimal.
