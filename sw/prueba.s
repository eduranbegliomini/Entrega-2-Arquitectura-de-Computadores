# Diagnostico de perifericos: LEDs siguen botones y display cuenta en hexadecimal.
# MMIO: display 0x80000000, LEDs 0x80000004, botones 0x80000008, contador 0x8000000C.
.section .text
.global _start
_start:
    lui  x1, 0x80000          # Base MMIO / display
    addi x2, x1, 4            # Registro LEDs
    addi x3, x1, 8            # Registro botones
    addi x4, x1, 12           # Contador de ciclos
    addi x5, x0, 0            # Contador hexadecimal del display
    lw   x6, 0(x4)            # Tiempo de referencia
    lui  x9, 0xBEC            # 12.500.000 ciclos = 0,5 s
    addi x9, x9, -992

prueba_loop:
    lw   x7, 0(x3)            # Leer botones sincronizados
    sw   x7, 0(x2)            # LEDs reflejan la mascara de botones
    lw   x8, 0(x4)            # Muestra actual del contador
    sub  x10, x8, x6          # Tiempo transcurrido desde la ultima cuenta
    bltu x10, x9, prueba_loop # Aun no transcurre medio segundo
    addi x5, x5, 1
    andi x5, x5, 255          # Contador hexadecimal de 00 a FF
    sw   x5, 0(x1)            # Mostrar conteo
    addi x6, x8, 0            # Nueva referencia temporal
    jal  x0, prueba_loop
