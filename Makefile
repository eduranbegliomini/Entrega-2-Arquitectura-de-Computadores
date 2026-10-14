TOP      := game_top
PCF      := goboard.pcf
RTL      := $(wildcard rtl/*.v)
JSON     := $(TOP).json
ASC      := $(TOP).asc
BIN      := $(TOP).bin
PYTHON   ?= python3

.PHONY: all bitstream prog clean test game
all: bitstream

sw/game.hex: sw/game.s tools/assembler.py
	$(MAKE) -C sw game.hex

game: sw/game.hex

$(JSON): $(RTL) sw/game.hex
	yosys -p 'read_verilog $(RTL); synth_ice40 -top $(TOP) -json $@; stat'

$(ASC): $(JSON) $(PCF)
	nextpnr-ice40 --hx1k --package vq100 --freq 25 --json $(JSON) --pcf $(PCF) --asc $@

$(BIN): $(ASC)
	icepack $(ASC) $@

bitstream: $(BIN)

prog: $(BIN)
	iceprog $(BIN)

test:
	$(PYTHON) -m unittest discover -s tests -v

clean:
	rm -f $(JSON) $(ASC) $(BIN)
	$(MAKE) -C sw clean
