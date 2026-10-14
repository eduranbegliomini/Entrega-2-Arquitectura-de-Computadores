# Proyecto 2 - Juego de reflejos sobre Pochoco SoC

## Contenido

- `rtl/`: Pochoco SoC, Espino Core, periféricos y `game_top`.
- `sw/game.s`: programa del juego en Assembly RV32E.
- `sw/game.hex`: código máquina generado por el assembler del proyecto.
- `tools/assembler.py`: assembler propio de dos pasadas; no invoca herramientas RISC-V externas.
- `tests/`: pruebas unitarias del assembler y comprobaciones estáticas.
- `docs/informe.pdf`: informe técnico para la entrega.
- `docs/informe.md`: fuente editable del informe.

## Requisitos de herramientas

Para regenerar `game.hex` se necesita Python 3.10 o posterior. Para sintetizar/programar la Go Board se necesitan las herramientas de la cadena open-source: Yosys, nextpnr-ice40, icepack e iceprog. El entorno en el que se preparó este paquete no tiene instaladas esas herramientas FPGA, de modo que la compilación física debe validarse en un computador con ellas y con la placa conectada.

## Regenerar el programa

Desde la carpeta raíz del proyecto:

```sh
make game
```

O, directamente:

```sh
python3 tools/assembler.py sw/game.s -o sw/game.hex
```

El archivo de salida contiene una palabra de 32 bits, como ocho dígitos hexadecimales, por línea. No se utiliza un assembler RISC-V externo.

### Ejemplo para modificar una constante durante la defensa

Para cambiar la preparación de 3 s a 2 s, en `sw/game.s` reemplaza las dos instrucciones que cargan 75.000.000 ciclos antes de `prep_wait`:

```asm
    lui  x6, 0x4787
    addi x6, x6, -1856
```

por las que cargan 50.000.000 ciclos:

```asm
    lui  x6, 0x2faf
    addi x6, x6, 128
```

Después ejecuta `make game` para regenerar `sw/game.hex` y vuelve a ejecutar las pruebas. Este cambio modifica solo la constante de preparación; no cambia la constante de 2.500.000 ciclos por décima.

## Ejecutar las pruebas disponibles

```sh
make test
```

También se puede ejecutar:

```sh
python3 -m unittest discover -s tests -v
```

Estas pruebas validan codificaciones conocidas, etiquetas, rangos, registros RV32E, instrucciones prohibidas y el formato/tamaño del archivo generado. No sustituyen una simulación RTL ni una prueba física en FPGA.

## Sintetizar y generar el bitstream

```sh
make bitstream
```

El flujo genera `game_top.json`, `game_top.asc` y `game_top.bin`. La selección de pines está en `goboard.pcf`, el módulo superior de síntesis es `game_top` y nextpnr recibe el objetivo de temporización `--freq 25` (25 MHz).

## Programar la Go Board

Con la placa conectada por USB y `iceprog` instalado:

```sh
make prog
```

Este comando programa el bitstream en la placa. No se ha ejecutado desde el entorno donde se creó este paquete.

## Mapa de memoria

| Dirección | Uso | Operación |
|---|---|---|
| `0x80000000` | Dos displays de siete segmentos | Escritura |
| `0x80000004` | Cuatro LEDs | Escritura |
| `0x80000008` | Cuatro botones | Lectura |
| `0x8000000C` | Contador libre de ciclos de 32 bits | Lectura |
| `0x80000010` | Marca temporal capturada al revelar el LED objetivo | Lectura |

El contador es reiniciado con el reset del SoC e incrementa una unidad por ciclo de `i_Clk`. Al escribir una máscara de un solo LED en el registro de LEDs, el hardware captura el contador en el registro de `0x80000010` en el mismo flanco de reloj que presenta el objetivo; el programa usa esa marca temporal para medir la respuesta. Las entradas de botones pasan por un sincronizador de dos registros; esto reduce el riesgo de metastabilidad, pero no reemplaza un filtro de rebote mecánico.

## Convenciones del juego

- Los cuatro LEDs permanecen encendidos al menos tres segundos al comenzar cada intento.
- Si se mantiene pulsado un botón durante la preparación, se espera a que se suelte antes de revelar el objetivo.
- El cronómetro se toma cuando se enciende solamente el LED objetivo. Esta interpretación separa los tres segundos de preparación del tiempo de reacción.
- Los tiempos se redondean a la décima más cercana. Los dos displays muestran dos dígitos decimales, por ejemplo `37` significa 3,7 segundos. El final de la medición es la lectura del contador que hace el programa tras detectar la pulsación; por ello incluye una pequeña latencia de sincronización y sondeo, muy inferior a una décima de segundo.
- `EE` indica botón incorrecto; la ronda se reinicia al soltar el botón y los aciertos acumulados se conservan.
- `FF` indica que el tiempo individual o el promedio redondea a 10,0 segundos o más. Los tiempos individuales se muestran en décimas; la suma del promedio acumula la duración exacta en ciclos, sin redondear cada respuesta.
- Tras diez aciertos, el promedio se redondea a la décima más cercana y queda mostrado indefinidamente con los LEDs apagados.

## Limitaciones y verificación pendiente

1. El código del assembler y sus pruebas unitarias se han ejecutado en Python. El archivo `game.hex` contiene 136 palabras, dentro de las 512 palabras de RAM configuradas por defecto.
2. La frecuencia de 25 MHz se basa en la documentación de la Go Board. A esa frecuencia, la preparación de tres segundos corresponde a 75.000.000 ciclos; una décima corresponde a 2.500.000 ciclos.
3. El RTL no ha podido sintetizarse o simularse en este entorno porque no se encontraron `yosys`, `nextpnr-ice40`, `icepack`, `iceprog`, `iverilog` ni `verilator` instalados.
4. Deben verificarse en la placa la polaridad/orden de los botones, el comportamiento del timer MMIO, la duración física de tres segundos y la respuesta real del CPU. No se afirma que esas pruebas físicas estén completadas.
