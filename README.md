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

## Compilar y programar el juego

Desde la raíz del proyecto, ejecuta:

```bat
build.bat
```

El script ensambla `sw/game.s` con `tools/assembler.py`, ejecuta las 14 pruebas, sintetiza el top `game_top`, ejecuta place-and-route, genera `game_top.bin` y programa la Go Board. Para evitar el problema de Yosys descrito en el informe, el flujo usa ABC con LUT4 en vez del paso ABC9.

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

Al comenzar cada ronda se encienden los cuatro LEDs durante tres segundos. Después se enciende un LED objetivo y se mide el tiempo de reacción. El tiempo individual se expresa en décimas de segundo; un botón incorrecto muestra `EE` y repite la ronda sin perder los aciertos anteriores. Tras diez aciertos se muestra el promedio, se apagan los LEDs y el programa queda en su bucle final, tal como está representado en el diagrama de flujo de `docs/informe.pdf`.

La constante de preparación de 3 s está cargada al comienzo de cada ronda porque `x6` se reutiliza para otros intervalos. El reset de encendido del SoC usa un contador de 20 bits para esperar aproximadamente 42 ms antes de liberar al procesador.
