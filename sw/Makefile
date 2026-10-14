PYTHON ?= python3
ASM := ../tools/assembler.py

.PHONY: all clean
all: game.hex

game.hex: game.s $(ASM)
	$(PYTHON) $(ASM) $< -o $@ --symbols game.symbols

clean:
	rm -f game.hex game.symbols
