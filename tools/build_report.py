#!/usr/bin/env python3
"""Generate the Spanish technical report PDF with ReportLab."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Preformatted, KeepTogether, Flowable
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "informe.pdf"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
pdfmetrics.registerFont(TTFont("DejaVu", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Mono", str(FONT_DIR / "DejaVuSansMono.ttf")))

NAVY = colors.HexColor("#16324F")
TEAL = colors.HexColor("#167D8D")
PALE = colors.HexColor("#EAF2F5")
PALE2 = colors.HexColor("#F5F7F8")
DARK = colors.HexColor("#263238")
MID = colors.HexColor("#58666E")
BORDER = colors.HexColor("#CAD5DB")
WARN = colors.HexColor("#FFF2D8")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitleX", fontName="DejaVu-Bold", fontSize=25, leading=31, textColor=NAVY, alignment=TA_LEFT, spaceAfter=12))
styles.add(ParagraphStyle(name="CoverSubX", fontName="DejaVu", fontSize=12, leading=18, textColor=MID, spaceAfter=7))
styles.add(ParagraphStyle(name="H1X", fontName="DejaVu-Bold", fontSize=16, leading=21, textColor=NAVY, spaceBefore=9, spaceAfter=8, keepWithNext=True))
styles.add(ParagraphStyle(name="H2X", fontName="DejaVu-Bold", fontSize=11.5, leading=15, textColor=TEAL, spaceBefore=7, spaceAfter=5, keepWithNext=True))
styles.add(ParagraphStyle(name="BodyX", fontName="DejaVu", fontSize=8.7, leading=12.5, textColor=DARK, spaceAfter=6))
styles.add(ParagraphStyle(name="SmallX", fontName="DejaVu", fontSize=7.3, leading=9.4, textColor=DARK, spaceAfter=2))
styles.add(ParagraphStyle(name="TableHeadX", fontName="DejaVu-Bold", fontSize=7.2, leading=9, textColor=colors.white))
styles.add(ParagraphStyle(name="TableCellX", fontName="DejaVu", fontSize=7.1, leading=9.2, textColor=DARK))
styles.add(ParagraphStyle(name="CodeX", fontName="DejaVu-Mono", fontSize=7.1, leading=9, textColor=DARK, leftIndent=3, rightIndent=3, backColor=PALE2, borderColor=BORDER, borderWidth=0.5, borderPadding=5, spaceBefore=4, spaceAfter=7))
styles.add(ParagraphStyle(name="CalloutX", fontName="DejaVu", fontSize=8.5, leading=12, textColor=DARK, backColor=WARN, borderColor=colors.HexColor("#E5BD69"), borderWidth=0.7, borderPadding=8, spaceBefore=5, spaceAfter=8))
styles.add(ParagraphStyle(name="FootX", fontName="DejaVu", fontSize=7, leading=8, textColor=MID, alignment=TA_CENTER))


def P(text, style="BodyX"):
    return Paragraph(text, styles[style])


def table(headers, rows, widths, font_size=7.1):
    data = [[P(str(x), "TableHeadX") for x in headers]]
    for row in rows:
        data.append([P(str(x), "TableCellX") for x in row])
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE2]),
    ]))
    return t


class ArchitectureDiagram(Flowable):
    def __init__(self, width=170*mm, height=37*mm):
        super().__init__()
        self.width, self.height = width, height

    def draw(self):
        c = self.canv
        def box(x, y, w, h, title, sub, fill=PALE):
            c.setFillColor(fill); c.setStrokeColor(BORDER)
            c.roundRect(x, y, w, h, 4, fill=1, stroke=1)
            c.setFillColor(NAVY); c.setFont("DejaVu-Bold", 8)
            c.drawCentredString(x+w/2, y+h-13, title)
            c.setFillColor(DARK); c.setFont("DejaVu", 6.8)
            for i, line in enumerate(sub.split("\n")):
                c.drawCentredString(x+w/2, y+h-25-i*9, line)
        def arrow(x1,y1,x2,y2):
            c.setStrokeColor(TEAL); c.setLineWidth(1.1); c.line(x1,y1,x2,y2)
            import math
            ang=math.atan2(y2-y1,x2-x1); length=5
            p1=(x2-length*math.cos(ang-0.45),y2-length*math.sin(ang-0.45))
            p2=(x2-length*math.cos(ang+0.45),y2-length*math.sin(ang+0.45))
            c.setFillColor(TEAL); c.setStrokeColor(TEAL)
            path=c.beginPath(); path.moveTo(x2,y2); path.lineTo(*p1); path.lineTo(*p2); path.close()
            c.drawPath(path,fill=1,stroke=0)
        box(8, self.height-32, 75, 26, "game_top", "módulo superior", fill=colors.HexColor("#DCE9F0"))
        box(95, self.height-32, 120, 26, "pochoco_soc", "bus + selección de direcciones", fill=colors.HexColor("#DCE9F0"))
        arrow(83, self.height-19, 95, self.height-19)
        y1=self.height-62
        box(3,y1,49,27,"Espino Core","RV32E")
        box(59,y1,49,27,"RAM","512 x 32")
        box(115,y1,49,27,"Periféricos","LED / botones")
        box(171,y1,49,27,"SPI","esclavo")
        arrow(145,self.height-32,27,y1+27)
        arrow(151,self.height-32,83,y1+27)
        arrow(157,self.height-32,139,y1+27)
        arrow(163,self.height-32,195,y1+27)
        c.setFillColor(MID); c.setFont("DejaVu", 6.5)
        c.drawString(4, self.height - 82, "Contador de ciclos accesible por MMIO en 0x8000000C.")


def footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    if doc.page > 1:
        canvas.setStrokeColor(BORDER)
        canvas.line(18*mm, h-14*mm, w-18*mm, h-14*mm)
        canvas.setFont("DejaVu", 7)
        canvas.setFillColor(MID)
        canvas.drawString(18*mm, h-11*mm, "Proyecto 2 · Juego de reflejos · Pochoco SoC")
        canvas.line(18*mm, 13*mm, w-18*mm, 13*mm)
        canvas.drawString(18*mm, 8*mm, "Informe técnico | Implementación no verificada físicamente en este entorno")
        canvas.drawRightString(w-18*mm, 8*mm, f"Página {doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(OUT), pagesize=A4,
    rightMargin=18*mm, leftMargin=18*mm, topMargin=20*mm, bottomMargin=19*mm,
    title="Informe técnico - Juego de reflejos Pochoco SoC",
    author="Proyecto 2 - Arquitectura de Computadores",
)
story=[]

# Cover
story += [Spacer(1, 18*mm), P("PROYECTO 2", "CoverSubX"), P("Juego de reflejos sobre<br/>Pochoco SoC", "CoverTitleX"), P("Informe técnico de arquitectura, Assembly, temporización y assembler propio", "CoverSubX"), Spacer(1, 10*mm)]
cover_data = [
    [P("Plataforma", "TableHeadX"), P("Nandland Go Board · Lattice iCE40 HX1K-VQ100", "TableCellX")],
    [P("Procesador", "TableHeadX"), P("Espino Core · subconjunto RV32E", "TableCellX")],
    [P("Programa", "TableHeadX"), P("sw/game.s → sw/game.hex", "TableCellX")],
    [P("Assembler", "TableHeadX"), P("tools/assembler.py · dos pasadas, sin assembler externo", "TableCellX")],
]
ct=Table(cover_data,colWidths=[33*mm,125*mm],hAlign="LEFT")
ct.setStyle(TableStyle([("BACKGROUND",(0,0),(0,-1),NAVY),("TEXTCOLOR",(0,0),(0,-1),colors.white),("BACKGROUND",(1,0),(1,-1),PALE2),("GRID",(0,0),(-1,-1),0.4,BORDER),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8)]))
story += [ct, Spacer(1, 12*mm), P("Estado de la entrega", "H2X"), P("El assembler propio genera 136 palabras y sus 14 pruebas unitarias pasan en este entorno. La síntesis RTL, la simulación de hardware y la programación física no se han ejecutado porque las herramientas FPGA no estaban instaladas; esas comprobaciones quedan identificadas explícitamente como pendientes.", "CalloutX"), Spacer(1, 20*mm), P("Documento de trabajo elaborado a partir del enunciado y del RTL entregado para el Proyecto 2.", "SmallX"), PageBreak()]

story += [P("1. Objetivo y requisitos funcionales", "H1X"), P("El juego debe encender los cuatro LEDs durante al menos tres segundos, seleccionar un objetivo, medir la respuesta al botón asociado y mostrar el tiempo en décimas de segundo. Se registran diez respuestas correctas; después se muestra su promedio. Una respuesta incorrecta indica error y reinicia el intento sin borrar los aciertos acumulados.")]
story += [table(["Requisito", "Respuesta de diseño", "Prueba prevista"], [
    ("Preparación ≥ 3 s", "Espera de 75.000.000 ciclos con los cuatro LEDs activos.", "Medir el contador entre inicio y salida de la espera."),
    ("Objetivo pseudoaleatorio", "LFSR de 8 bits, mezclado con el contador de ciclos.", "Observar secuencias entre varias partidas."),
    ("Respuesta correcta", "La lectura de botones debe coincidir exactamente con la máscara objetivo.", "Probar los cuatro índices LED/botón."),
    ("Respuesta incorrecta", "Mostrar EE, apagar LEDs, esperar liberación y reintentar.", "Verificar que contador y suma de aciertos se conservan."),
    ("Diez aciertos y promedio", "Acumular ciclos exactos y convertir la media a décimas al final.", "Comparar con cálculo manual de diez casos."),
], [32*mm, 66*mm, 60*mm]), Spacer(1,4*mm), P("Interpretación temporal: los tres segundos son una preparación previa. El cronómetro de reacción comienza cuando se revela el único LED objetivo. La interpretación se basa en que no tiene sentido incluir la espera de preparación en el tiempo que tarda el jugador en reaccionar.", "CalloutX")]

story += [P("2. Arquitectura del hardware", "H1X"), P("El módulo superior game_top instancia pochoco_soc y selecciona sw/game.hex como imagen de memoria. El SoC conecta el procesador Espino Core con la RAM unificada, los periféricos de la placa y el esclavo SPI. El contador libre se implementó dentro del módulo de periféricos en 0x0C. También se agregó una marca temporal en 0x10 que captura el contador en el mismo flanco de reloj que revela el LED objetivo.")]
story += [ArchitectureDiagram(), Spacer(1,1*mm), P("2.1 Mapa de memoria", "H2X"), table(["Dirección", "Uso", "Operación"], [
    ("0x80000000", "Dos displays de siete segmentos", "sw"),
    ("0x80000004", "Cuatro LEDs", "sw"),
    ("0x80000008", "Estado de los cuatro botones", "lw"),
    ("0x8000000C", "Contador de ciclos libre de 32 bits", "lw"),
    ("0x80000010", "Marca temporal del flanco que revela el objetivo", "lw"),
], [36*mm, 80*mm, 32*mm]), Spacer(1, 1.5*mm), P("El contador cycle_counter_q se reinicia con rst_ni y aumenta uno en cada flanco ascendente. Leer el offset 0x0C devuelve una muestra de su valor. Cuando se escribe una máscara one-hot en el registro de LEDs, target_start_counter_q captura cycle_counter_q en el mismo flanco que actualiza la salida de LEDs; Assembly lee esa marca en 0x10. Las entradas de botones atraviesan dos registros de sincronización para reducir el riesgo de metastabilidad; no se implementa un filtro de rebote mecánico.")]

story += [P("3. Temporización", "H1X"), P("La especificación publicada de Nandland Go Board declara un reloj integrado de 25 MHz. Por ello, el período es 1/25.000.000 s = 40 ns. El número de ciclos de un intervalo se calcula con N = frecuencia × tiempo.")]
story += [table(["Intervalo", "Cálculo", "Ciclos"], [
    ("1 segundo", "25.000.000 × 1", "25.000.000"),
    ("3 segundos", "25.000.000 × 3", "75.000.000"),
    ("0,1 segundo", "25.000.000 × 0,1", "2.500.000"),
    ("0,05 segundo", "25.000.000 × 0,05", "1.250.000"),
    ("Pausa final", "25.000.000 × 0,5", "12.500.000"),
], [33*mm, 72*mm, 43*mm]), P("El software usa diferencias modulares de un contador de 32 bits. Su período de desbordamiento es 2^32 / 25.000.000 ≈ 171,7987 s. Al consultar el contador frecuentemente, las diferencias de intervalos cortos permanecen válidas aunque el contador absoluto pase de 0xFFFFFFFF a cero.")]

story += [P("4. Flujo del juego", "H1X"), table(["Fase", "Funcionamiento"], [
    ("Liberar botón", "Se espera a que no haya ninguna entrada activa para evitar reutilizar una pulsación mantenida."),
    ("Preparación", "Se escribe 1111 en los LEDs y se espera 75.000.000 ciclos o más."),
    ("Protección de pulsaciones", "Si un botón se mantuvo durante la preparación, el objetivo no se revela hasta soltarlo."),
    ("Elegir objetivo", "Se mezcla el contador con el estado LFSR; el valor bajo de dos bits selecciona índice 0–3."),
    ("Mostrar y medir", "El LED objetivo cambia y el hardware captura el contador de inicio en el mismo flanco de reloj."),
    ("Validar", "Se compara la máscara de botones con la máscara del objetivo. Una respuesta incorrecta indica EE y repite."),
    ("Acierto", "Se redondea el residuo temporal, se muestra el tiempo y se agrega al total de aciertos."),
    ("Fin", "Tras diez aciertos se espera 0,5 s para mostrar la décima respuesta; luego se muestra el promedio y se apagan LEDs."),
], [37*mm, 111*mm])]

story += [P("5. Generación pseudoaleatoria", "H1X"), P("El estado se mantiene en ocho bits. Antes de elegir el objetivo, se combina mediante XOR con el byte bajo del contador leído tras la preparación y, si el estado queda en cero, se cambia a uno. En el paso LFSR, el bit 7 anterior sirve como realimentación; se calcula estado = (2 × estado) mod 256 y, si el bit alto era uno, se aplica XOR con 0x1D. El índice LED es estado AND 3.")]
story += [P("No se utiliza una instrucción SLL: duplicar el estado mediante ADD realiza el desplazamiento de un bit requerido por el LFSR y ANDI 255 conserva solo los ocho bits bajos. Una comprobación matemática independiente encontró que la actualización con máscara 0x1D recorre los 255 estados no nulos antes de repetirse. La mezcla con el contador añade dependencia del instante de lectura; no se trata de aleatoriedad criptográfica.", "BodyX"), P("En un sistema digital determinista que se reinicia al mismo estado, la primera selección puede coincidir entre arranques. Las selecciones siguientes mezclan lecturas del contador tomadas después de interacciones humanas de duración variable; la variación perceptible de secuencias debe confirmarse en varias partidas sobre la FPGA, como exige el enunciado.", "CalloutX")]

story += [P("6. Tiempo, displays y promedio", "H1X"), P("El programa cuenta décimas en software, avanzando el último límite exactamente 2.500.000 ciclos cada vez que se alcanza una nueva décima. La duración completa de la respuesta se calcula desde la marca temporal de hardware capturada al revelar el objetivo hasta la lectura del contador tras detectar la respuesta. Para mostrar el tiempo individual, el residuo respecto del último límite se compara con 1.250.000 ciclos y se redondea a la décima más cercana. El extremo final es la lectura del contador hecha tras detectar la pulsación por software, por lo que incluye una pequeña latencia de sincronización y sondeo; la resolución mostrada de 0,1 s es mucho mayor que esa latencia.")]
story += [P("Para convertir el valor de décimas a los dos dígitos, se resta diez repetidamente. El número de restas es el dígito de decenas y el residuo es el dígito de unidades. Se empaquetan como 16 × decenas + unidades. Esto es válido para dígitos 0–9; el decodificador de siete segmentos del SoC muestra cada nibble por separado.")]
story += [P("La suma acumula las duraciones exactas en ciclos, no los tiempos individuales redondeados. La media expresada en décimas equivale a suma_ciclos / 25.000.000: diez medidas se promedian y luego se convierten de segundos a décimas. Para redondear al décimo más cercano se suma la mitad del divisor (12.500.000 ciclos) antes de dividir por 25.000.000 mediante resta repetida. Si la suma ya alcanza 2.500.000.000 ciclos, la media de diez respuestas es al menos 10,0 s y se muestra FF; esto evita desbordar el acumulador antes de indicar el límite.", "CalloutX")]

story += [P("7. Assembler propio", "H1X"), P("tools/assembler.py es un assembler de dos pasadas. La primera analiza etiquetas y asigna direcciones de cuatro en cuatro bytes. La segunda codifica las instrucciones, resuelve los desplazamientos relativos de ramas y JAL y genera una palabra hexadecimal de ocho dígitos por línea. No invoca un assembler RISC-V externo.")]
story += [table(["Aspecto", "Sintaxis / validación"], [
    ("Registros", "x0 a x15; registros x16–x31 se rechazan."),
    ("Instrucciones", "lui, addi, andi, xori, add, sub, and, xor, lw, sw, beq, bne, bltu, jal."),
    ("Inmediatos", "Decimal o hexadecimal; validación de rango de 12 bits con signo, 20 bits U y desplazamientos B/J."),
    ("Memoria", "offset(xN), por ejemplo lw x12, 0(x4)."),
    ("Etiquetas", "Etiquetas hacia delante/atrás se resuelven en la segunda pasada."),
    ("Directivas", "Se ignoran .section, .text, .global, .globl, .type y .size."),
    ("Rechazos", "Instrucciones no soportadas, sintaxis incorrecta, campos fuera de rango e instrucciones de shift."),
], [36*mm, 112*mm]), Spacer(1, 1.5*mm)]
story += [P("Ejemplo de codificación: addi x1, x0, 1 produce 0x00100093. El opcode 0x13 identifica operaciones inmediatas; rd es x1, funct3 = 000 indica ADDI, rs1 es x0 y el inmediato es uno. El archivo game.hex contiene 136 palabras, menor que las 512 palabras de la RAM configurada.")]

story += [P("8. Construcción", "H1X"), P("Desde la raíz del proyecto, los comandos previstos son:")]
story += [Preformatted("make game       # assembler propio: sw/game.s -> sw/game.hex\nmake test       # pruebas unitarias del assembler\nmake bitstream  # Yosys + nextpnr-ice40 (--freq 25) + icepack\nmake prog       # programa la FPGA mediante iceprog", styles["CodeX"])]
story += [P("El módulo superior seleccionado es game_top. El Makefile utiliza los archivos de rtl/ y depende de sw/game.hex para sintetizar la memoria inicializada. nextpnr-ice40 se configura con objetivo de 25 MHz. El PCF conserva reloj, cuatro LEDs, cuatro botones, ambos displays y las señales SPI; no incluye asignaciones UART porque game_top no tiene puertos UART.")]
story += [P("Cambio de una constante para la defensa", "H2X"), P("Para cambiar la preparación de 3 s a 2 s, reemplazar en sw/game.s la pareja que carga 75.000.000 ciclos por la pareja que carga 50.000.000 ciclos. Después ejecutar make game para regenerar sw/game.hex con el assembler propio.", "BodyX"), Preformatted("# Antes: 3 s = 75.000.000 ciclos\nlui  x6, 0x4787\naddi x6, x6, -1856\n\n# Después: 2 s = 50.000.000 ciclos\nlui  x6, 0x2faf\naddi x6, x6, 128", styles["CodeX"])]

story += [P("9. Verificación y limitaciones", "H1X"), table(["Prueba", "Resultado disponible", "Estado"], [
    ("Assembler de game.s", "Genera 136 palabras de 32 bits.", "Verificado en Python"),
    ("Codificaciones conocidas", "ADDI, LUI, LW, SW, JAL y BNE contrastadas con palabras de referencia.", "14 pruebas unitarias pasan"),
    ("Etiquetas y rangos", "Saltos hacia delante/atrás, límites RV32E e inmediatos inválidos.", "Verificado en pruebas unitarias"),
    ("Temporización", "Constantes 75.000.000, 2.500.000, 1.250.000, 12.500.000, 25.000.000 y límite 2.500.000.000 comprobados aritméticamente.", "Verificado por cálculo"),
    ("Síntesis RTL", "Yosys no está instalado en este entorno.", "Pendiente"),
    ("Simulación RTL", "Icarus Verilog y Verilator no están instalados.", "Pendiente"),
    ("Prueba física", "No se dispuso de la Go Board conectada.", "Pendiente"),
], [34*mm, 83*mm, 31*mm]), Spacer(1,3*mm), P("Antes de entregar, ejecutar síntesis, place-and-route y programación en el computador con la cadena FPGA. En la Go Board se deben probar: preparación de tres segundos, los cuatro pares LED/botón, respuesta correcta y tiempo mostrado, error y reinicio sin perder aciertos, diez aciertos y promedio, variación de secuencias y regeneración de game.hex tras cambiar una constante.", "CalloutX")]

story += [P("10. Referencias", "H1X"), P("1. Enunciado del Proyecto 2, “Juego en Assembly sobre Pochoco SoC”, Universidad de los Andes, semestre 2026-2.", "SmallX"), P("2. README y RTL de Pochoco SoC / Espino Core entregados como material de partida.", "SmallX"), P('3. Nandland, “The Go Board”, especificación de reloj integrado de 25 MHz: <link href="https://nandland.com/the-go-board/" color="#167D8D">https://nandland.com/the-go-board/</link>.', "SmallX"), P('4. Nandland, “Project 3 - The Flip-Flop (AKA Register)”, explicación de frecuencia, período de reloj y temporización: <link href="https://nandland.com/project-3-the-flip-flop-aka-register/" color="#167D8D">https://nandland.com/project-3-the-flip-flop-aka-register/</link>.', "SmallX")]

doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f"Created {OUT} ({OUT.stat().st_size} bytes)")
