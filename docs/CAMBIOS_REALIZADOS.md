# Cambios aplicados a la primera versión

## Correcciones descritas en los cambios de la compañera

1. `sw/game.s`: las dos instrucciones que cargan 75.000.000 ciclos (3 s) ya no se ejecutan solo al encender. Se ejecutan inmediatamente después de `wait_release`, al comienzo de cada ronda. La razón es que `x6` luego se reutiliza para 1.250.000 ciclos (0,05 s) y para la pausa final de 12.500.000 ciclos (0,5 s).
2. `rtl/pochoco_soc.v`: el contador de reset de encendido cambió de 4 bits a 20 bits. A 25 MHz, 1.048.575 ciclos equivalen aproximadamente a 41,94 ms.
3. `build.bat`: crea el hex con el assembler propio, ejecuta las 14 pruebas para el juego normal, usa el flujo ABC LUT4 de Yosys, ejecuta nextpnr, crea el bitstream y programa la placa. El argumento `prueba` usa `sw/prueba.s` y omite la suite de pruebas del juego porque el hex contiene deliberadamente otro programa.
4. `sw/prueba.s`: diagnóstico SoC que refleja el valor de los botones en los LEDs y muestra `A` junto al nibble de botones en los displays.
5. `test_placa/test_placa.v` y `test_placa.bat`: diagnóstico independiente del procesador; los LEDs reflejan los botones y los displays cuentan hexadecimal cada medio segundo.

## Corrección adicional para reiniciar una partida

La primera versión terminaba en un bucle infinito `done_loop`. Para cumplir el requisito de poder volver a jugar, se sustituyó ese bucle por la espera de una nueva pulsación y su liberación, y después un salto a `_start`. Esto vuelve a inicializar el contador de aciertos, la suma y la semilla. Por esta adición el programa tiene 140 palabras, no 136, y se actualizó la aserción de tamaño correspondiente en `tests/test_assembler.py`. El assembler como tal no fue modificado.

## Estado de validación

En este entorno se confirmó que el assembler genera 140 palabras para `sw/game.s`, 12 para `sw/prueba.s` y que pasan las 14 pruebas unitarias. No se pudo ejecutar aquí la síntesis FPGA ni probar físicamente esta copia en la Go Board; hay que verificar esas etapas en el equipo con OSS CAD Suite y placa conectada.
