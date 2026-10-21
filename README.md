# Proyecto 2: Juego de reflejos sobre Pochoco SoC

Proyecto de Arquitectura de Computadores: juego de reflejos en Assembly para el Espino Core del Pochoco SoC, implementado sobre una Nandland Go Board con FPGA Lattice iCE40 HX1K-VQ100.

El informe técnico de entrega está en `docs/informe.pdf`. Según ese informe, el juego fue probado en la placa y funciona.

## Archivos principales

- `sw/game.s`: juego en Assembly RV32E.
- `sw/game.hex`: instrucciones máquina generadas por el assembler propio.
- `tools/assembler.py`: assembler de dos pasadas.
- `tests/test_assembler.py`: 14 pruebas unitarias del assembler y verificaciones estáticas.
- `rtl/pochoco_soc.v`: SoC con reset de encendido extendido a un contador de 20 bits (~42 ms a 25 MHz).
- `rtl/pochoco_periph.v`: display, LEDs, botones sincronizados, contador de ciclos y marca de inicio del LED objetivo.
- `rtl/game_top.v`: módulo superior conectado a los pines definidos en `goboard.pcf`.
- `sw/prueba.s`: diagnóstico del SoC; los LEDs siguen a los botones y el display cuenta en hexadecimal.
- `test_placa/test_placa.v` y `test_placa.bat`: diagnóstico sin procesador para revisar reloj, displays, LEDs, botones y programación.
- `docs/informe.pdf`: informe técnico de cinco páginas.

## Herramientas

Ejecuta los scripts desde la consola de OSS CAD Suite para Windows, con `python`, `yosys`, `nextpnr-ice40`, `icepack` e `iceprog` disponibles en el `PATH`.

### Regenerar `game.hex` desde `game.s`

Para generar el código máquina a partir del programa Assembly, ejecuta desde la raíz del proyecto:

```bat
python tools\assembler.py sw\game.s -o sw\game.hex --symbols sw\game.symbols
```

Este comando ejecuta el assembler propio y genera `sw/game.hex`, con las instrucciones máquina que cargará el procesador. También genera `sw/game.symbols`, con la información de las etiquetas.

### Sintetizar y programar la FPGA

Para ejecutar el flujo completo de compilación y programación de la Go Board, ejecuta:

```bat
build.bat
```

El script ensambla `sw/game.s`, ejecuta las 14 pruebas unitarias, sintetiza el módulo superior `game_top`, realiza la etapa de *place-and-route*, genera el bitstream `game_top.bin` y programa la FPGA Lattice iCE40 HX1K-VQ100 de la Go Board.

El flujo utiliza ABC con LUT4 en lugar de ABC9 para evitar el problema de Yosys documentado en el informe.

Si modificas `sw/game.s`, vuelve a ejecutar `build.bat` para regenerar el código máquina, volver a comprobar el proyecto y programar la nueva versión en la placa.

## Diagnósticos de hardware

Para programar la variante de diagnóstico basada en el SoC:

```bat
build.bat prueba
```

En esta variante los LEDs reflejan los botones y el display cuenta en hexadecimal. Para regresar al juego, vuelve a ejecutar `build.bat` sin argumentos.

Para programar el diagnóstico independiente del procesador:

```bat
test_placa.bat
```

En este diseño los LEDs reflejan directamente las entradas de los botones y los displays cuentan en hexadecimal. Para regresar al juego, ejecuta nuevamente `build.bat`.

## Ejecutar las pruebas unitarias

```bat
python -m unittest discover -s tests -v
```

Las 14 pruebas cubren codificaciones, etiquetas, restricciones de registros e inmediatos, instrucciones no soportadas, el tamaño del juego en RAM y aspectos estáticos del programa. El informe describe los ensayos efectuados en la placa.

## Mapa de memoria MMIO

| Dirección | Uso | Acceso |
|---|---|---|
| `0x80000000` | Dos displays de siete segmentos | Escritura |
| `0x80000004` | Cuatro LEDs | Escritura |
| `0x80000008` | Cuatro botones | Lectura |
| `0x8000000C` | Contador de ciclos de 32 bits | Lectura |
| `0x80000010` | Marca temporal al encender el LED objetivo | Lectura |

## Funcionamiento documentado

El juego utiliza un reloj de 25 MHz, por lo que cada ciclo dura 40 ns y se producen 25.000.000 de ciclos por segundo. Al comenzar cada ronda, los cuatro LEDs permanecen encendidos durante al menos tres segundos, equivalentes a 75.000.000 de ciclos. Después, se selecciona un LED objetivo mediante un generador pseudoaleatorio basado en un LFSR de 8 bits, combinado con información del contador de ciclos.

La medición de la respuesta comienza en el mismo flanco de reloj en que el periférico registra la escritura de la máscara del LED objetivo. El programa consulta el contador de ciclos y convierte el tiempo de reacción a décimas de segundo utilizando 2.500.000 ciclos por décima.

Si se presiona un botón incorrecto, el display muestra `EE` y se reinicia la ronda actual sin perder las respuestas correctas acumuladas. El juego continúa hasta obtener diez respuestas correctas. Después calcula y muestra el promedio de los diez tiempos, expresado en décimas de segundo, y el programa queda en un bucle final.

El promedio se calcula a partir de los ciclos acumulados de las respuestas correctas, antes de redondear los tiempos individuales. Esto evita que el promedio dependa de la suma de los valores individuales ya redondeados.

La constante correspondiente a la preparación de tres segundos se carga al comienzo de cada ronda porque el registro `x6` se reutiliza para otros intervalos. El reset de encendido del SoC utiliza un contador de 20 bits para esperar aproximadamente 42 ms a 25 MHz antes de liberar al procesador.

Después de completar las diez respuestas correctas, el programa no implementa un reinicio mediante botón. Para iniciar otra partida, vuelve a programar el juego ejecutando `build.bat`.
