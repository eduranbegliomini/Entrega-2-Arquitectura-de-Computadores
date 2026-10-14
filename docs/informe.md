# Proyecto 2: Juego de reflejos sobre Pochoco SoC

**Asignatura:** Arquitectura de Computadores  
**Plataforma:** Nandland Go Board, FPGA Lattice iCE40 HX1K-VQ100  
**Procesador:** Espino Core, subconjunto RV32E  
**Programa:** `sw/game.s`  
**Assembler propio:** `tools/assembler.py`

## 1. Objetivo

Implementar un juego en el que el hardware enciende los cuatro LEDs durante al menos tres segundos, revela un LED objetivo, mide la respuesta del botón asociado y muestra el tiempo en décimas de segundo. El juego registra diez respuestas correctas y presenta su promedio. Una respuesta incorrecta se indica como error y reinicia el intento actual sin borrar los aciertos ya registrados.

El proyecto incluye tres piezas que cooperan: (1) el SoC en Verilog, que proporciona el procesador, RAM y periféricos; (2) el programa Assembly que controla la lógica del juego; y (3) el assembler del grupo, que transforma el fuente del juego en el archivo hexadecimal cargado por la RAM.

## 2. Arquitectura

`game_top` es el módulo superior seleccionado por síntesis. Instancia `pochoco_soc` y le asigna `MemFile = "sw/game.hex"`. El SoC instancia el Espino Core, la RAM unificada, los periféricos y el esclavo SPI. Las señales de reloj, LEDs, botones, displays y SPI están expuestas con nombres compatibles con `goboard.pcf`.

El SoC decide si una dirección corresponde a RAM o a MMIO a partir del bit 31. Dentro del espacio MMIO, `data_addr[16]` separa los periféricos de placa del esclavo SPI. El contador se añadió al periférico ya existente, aprovechando una palabra MMIO libre.

### 2.1 Mapa de memoria utilizado

| Dirección | Offset MMIO | Función | Acceso desde el programa |
|---|---:|---|---|
| `0x80000000` | `0x00` | Registro de dos dígitos del display | `sw` |
| `0x80000004` | `0x04` | Registro de cuatro LEDs | `sw` |
| `0x80000008` | `0x08` | Estado de cuatro botones | `lw` |
| `0x8000000C` | `0x0C` | Contador de ciclos de 32 bits | `lw` |
| `0x80000010` | `0x10` | Marca temporal capturada al revelar el objetivo | `lw` |

En `pochoco_periph.v` se añadió `cycle_counter_q`, que se pone a cero durante el reset y se incrementa en cada flanco ascendente del reloj. Una lectura del offset `0x0C` devuelve el contador libre. Además, cuando se escribe una máscara de un solo LED en el registro de LEDs, `target_start_counter_q` captura el contador en el mismo flanco de reloj que actualiza la salida de LEDs. El programa lee esa marca temporal en `0x10`, por lo que el cronómetro comienza en el mismo evento lógico de hardware que revela el objetivo.

Las entradas de botones pasan por dos registros de sincronización antes de que el software pueda leerlas. Esto reduce el riesgo de metastabilidad al cruzar desde señales asíncronas al reloj del SoC, pero no constituye un filtro de rebote mecánico.

### 2.2 Reset y periféricos

El reset de encendido del SoC mantiene el procesador en reset durante los primeros ciclos de reloj; el contador de ciclos del periférico se reinicia durante ese intervalo. Los LEDs usan cuatro bits y los botones se leen como un registro de cuatro bits. El decodificador existente acepta valores hexadecimales `0`–`F`; por eso `EE` se utiliza como indicador de error y `FF` como indicador de que el tiempo excede el rango numérico de dos dígitos decimales.

## 3. Frecuencia y conversión de tiempo

La documentación de la Nandland Go Board especifica un reloj de placa de 25 MHz. El período correspondiente es:

\[
T_{clk}=\frac{1}{25\,000\,000}=40\text{ ns}
\]

Para un intervalo de duración \(t\), el número aproximado de ciclos es \(N=f_{clk}t\).

| Intervalo | Cálculo | Ciclos |
|---|---:|---:|
| 1 segundo | \(25\,000\,000\times1\) | 25.000.000 |
| 3 segundos de preparación | \(25\,000\,000\times3\) | 75.000.000 |
| 0,1 segundos (una décima) | \(25\,000\,000\times0,1\) | 2.500.000 |
| 0,05 segundos (umbral de redondeo) | \(25\,000\,000\times0,05\) | 1.250.000 |

La espera de preparación comprueba repetidamente `contador_actual - contador_inicio` y no pasa al estímulo hasta que la diferencia es al menos 75.000.000. Se utiliza resta de 32 bits; la diferencia modular sigue siendo correcta para intervalos menores que una vuelta completa del contador.

El contador de 32 bits se desborda después de:

\[
\frac{2^{32}}{25\,000\,000}\approx171,7987\text{ s}
\]

Como el software lo consulta de forma frecuente, los intervalos cortos pueden medirse atravesando el desbordamiento sin depender de que el contador absoluto aumente de forma ilimitada. La implementación debe evitar que exista una pausa única entre lecturas próxima a una vuelta completa.

## 4. Máquina de estados del juego

El flujo implementado puede describirse mediante los siguientes estados lógicos:

1. **Esperar liberación:** se evita que un botón mantenido de una ronda anterior se vuelva a contar.
2. **Preparación:** se escriben `1111` en el registro de LEDs y se esperan al menos tres segundos.
3. **Liberar botones antes del estímulo:** si se pulsó un botón durante la preparación y sigue presionado, el objetivo no se revela todavía.
4. **Elegir objetivo:** se mezcla el estado pseudoaleatorio con el byte bajo del contador y se actualiza un LFSR de ocho bits.
5. **Revelar objetivo:** se construye una máscara de un solo bit y se escribe al registro de LEDs. El hardware captura el contador en el mismo flanco que actualiza los LEDs, y Assembly lee esa marca temporal como inicio de la medición.
6. **Esperar y medir:** el software lee el contador y los botones. Cada 2.500.000 ciclos incrementa el contador de décimas.
7. **Respuesta correcta:** se exige que el registro de botones sea exactamente igual a la máscara del objetivo, se redondea la fracción restante a la décima más cercana, se muestra el tiempo y se acumula.
8. **Respuesta incorrecta:** se muestra `EE`, se apagan los LEDs y se espera que se libere el botón; los aciertos y su suma se conservan.
9. **Promedio:** tras diez aciertos, se calcula el promedio a partir de la suma de ciclos exactos. La conversión a décimas y el redondeo se realizan al final; después se muestra el promedio y se apagan los LEDs.

La interpretación aplicada es que los tres segundos son una preparación previa y el instante de inicio de la medición es la aparición del único LED objetivo. Esto tiene sentido para medir tiempo de reacción: el jugador no puede reaccionar al objetivo antes de que este sea revelado. Esta interpretación se debe explicar durante la defensa porque el enunciado no especifica con total precisión cómo separar “inicio de ronda” e inicio del cronómetro.

## 5. Generación pseudoaleatoria

El software conserva un estado de ocho bits. Antes de elegir el objetivo, lo combina mediante XOR con los ocho bits menos significativos de una lectura del contador de ciclos. Si el estado resultante es cero, se cambia a uno, ya que un LFSR que parte de cero no evoluciona.

La actualización toma el bit 7 anterior como realimentación, desplaza el estado a la izquierda y, si el bit de realimentación estaba activo, aplica XOR con `0x1D`. El desplazamiento por software se realiza duplicando el valor con `add` y limitando el resultado a ocho bits mediante `andi 255`; esto evita las instrucciones de desplazamiento deshabilitadas en la ALU proporcionada. La máscara de LED se construye duplicando el valor uno entre cero y tres veces.

El polinomio/máscara `0x1D` produce un ciclo de 255 estados no nulos para esta variante de LFSR de ocho bits. La mezcla del contador hace que las selecciones posteriores dependan del instante de lectura tras la interacción humana, cuyo tiempo varía entre intentos. No es aleatoriedad criptográfica ni una fuente de entropía demostrada. Al reiniciar toda la lógica al mismo estado, la primera selección puede coincidir entre partidas; lo que se debe comprobar es que la secuencia completa no quede fijada y se observe variación en partidas reales.

## 6. Unidad temporal, displays y promedio

Una décima corresponde a 2.500.000 ciclos. El programa conserva un límite temporal `last_tick` y aumenta el contador de décimas cuando han transcurrido al menos 2.500.000 ciclos desde ese límite, avanzándolo exactamente esa cantidad. Para mostrar el tiempo individual, compara el residuo con 1.250.000 ciclos y redondea a la décima más cercana. En paralelo, conserva la diferencia completa entre la marca temporal del objetivo y la lectura del contador realizada inmediatamente después de que el programa detecta la respuesta. Por tanto, la suma conserva precisión de ciclos sin redondeo por intento, aunque incluye una pequeña latencia de sincronización y sondeo del botón; no es una captura de hardware exacta del contacto físico.

Los dos displays están codificados por un byte, un dígito por nibble. Para mostrar una medida `d` en décimas, se divide repetidamente por diez: el cociente da el dígito de las decenas y el residuo da las unidades. El byte se forma como `16 × decenas + unidades`, equivalente a colocar cada dígito decimal en su nibble. No se utiliza división hardware, que no está implementada: se usa resta repetida por diez.

El acumulador guarda la suma de los ciclos exactos de las diez respuestas. La media expresada en décimas se obtiene dividiendo esa suma por 25.000.000, ya que se divide por diez respuestas y se convierte de segundos a décimas. Para redondear al décimo más cercano se suma la mitad del divisor, 12.500.000 ciclos, antes de la división entera. Así no se pierde precisión redondeando cada respuesta individual antes de promediar.

Los displays solo pueden mostrar dos dígitos, de `00` a `99` décimas (0,0 a 9,9 s). `FF` indica que un tiempo individual o el promedio redondea a 100 décimas (10,0 s) o más. El acumulador de promedio mantiene ciclos exactos y se satura con un marcador si la suma ya implica que la media alcanzará ese límite.

## 7. Assembler propio

El programa `tools/assembler.py` implementa un assembler de dos pasadas:

- En la primera pasada limpia comentarios, reconoce etiquetas, ignora las directivas de sección/global permitidas y asigna a cada instrucción una dirección de cuatro en cuatro bytes.
- En la segunda pasada convierte las instrucciones a palabras de 32 bits. Los destinos de las ramas y `jal` se calculan como desplazamientos relativos a la dirección de la instrucción.
- Se escribe una palabra por línea, usando ocho dígitos hexadecimales, sin prefijo `0x`, formato adecuado para `$readmemh`.
- No se ejecuta `as`, `ld`, `objcopy` ni ninguna otra herramienta de ensamblado RISC-V externo.

### 7.1 Sintaxis soportada

- Registros: `x0` a `x15`.
- Instrucciones: `lui`, `addi`, `andi`, `xori`, `add`, `sub`, `and`, `xor`, `lw`, `sw`, `beq`, `bne`, `bltu` y `jal`.
- Comentarios con `#` o `;`.
- Etiquetas con nombre, por ejemplo `wait_loop:`.
- Memoria en formato `offset(xN)`, por ejemplo `lw x12, 0(x4)`.
- Inmediatos decimales, negativos o hexadecimales; los campos se validan según su ancho.
- Directivas ignoradas: `.section`, `.text`, `.global`, `.globl`, `.type` y `.size`.

No se aceptan pseudoinstrucciones ni instrucciones de desplazamiento porque el programa no las necesita y la ALU entregada no implementa la operación de desplazamiento. Los errores de sintaxis, registros fuera del conjunto RV32E, inmediatos fuera de rango, directivas no soportadas e instrucciones desconocidas generan un mensaje de error.

### 7.2 Ejemplo de traducción

`addi x1, x0, 1` se codifica como `0x00100093`:

- opcode `0010011` para operaciones inmediatas;
- `rd = x1`;
- `funct3 = 000` para `ADDI`;
- `rs1 = x0`;
- inmediato de 12 bits igual a uno.

El programa de ejemplo `lui x2, 0x80000` se codifica como `0x80000137` y prepara la base MMIO en `x2` si se usa como destino. El assembler se prueba con instrucciones conocidas y con etiquetas hacia delante y hacia atrás.

## 8. Construcción y comandos

Desde la raíz del proyecto:

```sh
make game       # genera sw/game.hex con el assembler propio
make test       # ejecuta pruebas unitarias del assembler
make bitstream  # sintetiza y genera game_top.bin
make prog       # programa la Go Board conectada
```

El flujo FPGA utiliza Yosys (`synth_ice40`), nextpnr-ice40 (con objetivo de 25 MHz), icepack e iceprog. El PCF del proyecto no conserva las asignaciones UART originales porque los puertos UART no forman parte de `game_top`; mantiene los pines para reloj, LEDs, botones, displays y SPI.

### Cambio de una constante para la defensa

Por ejemplo, para cambiar la preparación de 3 s a 2 s, sustituir en `sw/game.s` la pareja que carga 75.000.000 ciclos:

```asm
lui  x6, 0x4787
addi x6, x6, -1856
```

por la pareja que carga 50.000.000 ciclos:

```asm
lui  x6, 0x2faf
addi x6, x6, 128
```

Después ejecutar `make game`, que regenera `sw/game.hex` con el assembler propio. Esta demostración cambia la preparación sin modificar la conversión de 2.500.000 ciclos por décima.

## 9. Pruebas y estado de verificación

### 9.1 Pruebas ejecutadas en este entorno

- Ejecución del assembler propio sobre `sw/game.s`.
- Generación de 136 palabras hexadecimales, cada una de ocho dígitos.
- Verificación de que el programa cabe en la RAM de 512 palabras configurada por defecto.
- Pruebas unitarias de codificaciones conocidas (`addi`, `lui`, `lw`, `sw`, `jal` y una rama `bne` hacia atrás).
- Pruebas de etiquetas hacia delante y atrás, límites de registros RV32E, rangos de inmediatos y rechazo de una instrucción `slli` no soportada por este proyecto.
- Comprobación matemática de 3 s, una décima, el umbral de redondeo, 25.000.000 ciclos por promedio en décimas y el límite de 2.500.000.000 ciclos.

### 9.2 Pruebas pendientes

En el entorno de generación no estaban instalados `yosys`, `nextpnr-ice40`, `icepack`, `iceprog`, `iverilog` ni `verilator`. Por eso no se afirma que se haya completado la síntesis, una simulación RTL o la programación física. Antes de la entrega final se debe ejecutar el flujo en la máquina con la cadena FPGA y verificar:

1. La compilación y síntesis del módulo `game_top`.
2. La programación de la placa y el encendido de los cuatro LEDs durante al menos tres segundos.
3. Los cuatro objetivos y su correspondencia con los cuatro botones.
4. Una respuesta correcta, un botón incorrecto y la conservación del progreso.
5. Diez respuestas correctas, la suma y el promedio mostrado.
6. Variación perceptible de los objetivos entre partidas.
7. La regeneración de `game.hex` después de cambiar una constante.

## 10. Referencias

- Enunciado del Proyecto 2, *Juego en Assembly sobre Pochoco SoC*, Universidad de los Andes, semestre 2026-2.
- README original de Pochoco SoC y Espino Core suministrado con el proyecto.
- Nandland, “The Go Board”, especificaciones de la placa y reloj integrado de 25 MHz: https://nandland.com/the-go-board/
- Nandland, “Project 3 – The Flip-Flop (AKA Register)”, explicación del reloj de la Go Board: https://nandland.com/project-3-the-flip-flop-aka-register/
