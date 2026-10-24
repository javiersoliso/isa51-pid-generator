# Instrument and loop index (revision 4)

Every tag that appears on [`drawings/pid_spinning_line_rev4.dxf`](../drawings/pid_spinning_line_rev4.dxf), grouped by loop. The tag letters are explained in [`isa51-tag-notation.md`](isa51-tag-notation.md). `*` = assumed, not confirmed in the plant. Controller input/output addresses (modules, slots, terminals) are deliberately left out.

## Area 02: spinning (spin beam, quench, finish and pulling rolls)

| # | Loop | Primary element | Signals on the drawing | Type | Final element / drive |
|---|---|---|---|---|---|
| 1 | Metering pump 1 speed | `SNM-02` speed from a tachogenerator (wired analog input) | `STD-02` speed reference 4–20 mA, `NCD-02` start/stop, `XSR/XSF-02` run/fault, `SNL-02` speed on screen | Control | `VFD-10` (existing drive) → motor `ME-B1` |
| 2 | Metering pump 2 speed | `ST-03` speed read from the drive over the bus | `STD-03`, `NCD-03`; bus: `IN-03`, `SNM-03`, `XSR-03`, `XSF-03` | Control | `VFD-11` (retrofit*) → motor `ME-B2` |
| 3 | Melt pressure, spinneret 1 | `PTB-03` melt pressure transmitter | `PIA-03` indication and high alarm (`PAH` 180 bar*); operating range 120–150 bar | Indication + alarm | – |
| 4 | Melt pressure, spinneret 2 | `PTB-04` | `PIA-04` | Indication + alarm | – |
| 5 | Thermal oil temperature (spin beam heating) | `TEB-08` thermocouple in the thermal oil tank | `TI/TN-08` value and set point on screen, `TY-07` heater relay, `LSL-02` low level → `MF-02` general alarm, `NS-03` recirculation pump contactor | Control | Electric heaters of the tank; recirculation pump |
| 6 | Quench fan 1 speed | `SNM-04` measured speed | `ST-04` speed reference (manual set point), `NC-04` start/stop, `XSR/XSF-04` | Control (manual reference) | `VFD-V1*` → motor `ME-V1` |
| 7 | Quench fan 2 speed | `SNM-05` | `ST-05`, `NC-05`, `XSR/XSF-05` | Control (manual reference) | `VFD-V2*` → motor `ME-V2` |
| 8 | Quench air temperature, duct 1 | `TEB-09` thermocouple in the 6 in. air duct | `TI-09` | Indication | – |
| 9 | Quench air temperature, duct 2 | `TEB-10` | `TI-10` | Indication | – |
| 10 | Fume extractor | – | `NC-06` start/stop, `XSR/XSF-06` run/fault | On/off + status | Contactor → motor `ME-EX` |
| 11 | Finish roll 1 speed | Speed read from the drive over the bus | `STD-04` reference, `NCD-07` start/stop; bus: `IN-06`, `SNM-06`, `XSR-07`, `XSF-07` | Control | `VFD-F1*` → motor `ME-F1` |
| 12 | Finish roll 2 speed | idem | `STD-05`, `NCD-08`; bus: `IN-07`, `SNM-07`, `XSR-08`, `XSF-08` | Control | `VFD-F2*` → motor `ME-F2` |
| 13 | Pulling roll 1 speed | idem | `STD-09`, `NCD-09`; bus: `IN-02`, `SNM-08`, `XSR-09`, `XSF-09` | Control | `VFD-P1*` → motor `ME-P1` |
| 14 | Pulling roll 2 speed | idem | `STD-10`, `NCD-10`; bus: `IN-08`, `SNM-09`, `XSR-10`, `XSF-10` | Control | `VFD-P2*` → motor `ME-P2` |
| 15 | Spin-finish tray position | `ZSB-14`, `ZSB-15` limit switches (tray up / down) | Digital inputs to the controller | Position status | – |
| 16 | Spin-finish oil pump | – | `NCD-04` start/stop | On/off | Contactor → motor `ME-AL` |
| P1 | **Proposal:** humidity / dew point of the quench air | `MT-01*`, `MT-02*` at each fan intake | `MI-01*`, `MI-02*` | Indication (proposed improvement) | – |
| S1 | **Assumption:** melt overpressure protection | `PSE-01*`, `PSE-02*` rupture discs at each metering pump outlet | – | Self-actuated safety device | – |

Summary for area 02: 16 loops (9 speed or temperature control loops, 4 indication or alarm loops, 2 on/off loops with status, 1 position status), plus 1 proposed measurement and 1 assumed safety device.

## Area 01: extruder (redrawn from another team's drawing)

| Loop | Primary element | Function in the controller | Final element |
|---|---|---|---|
| Barrel zones 0 to 6 temperature (7 loops) | `TE-0101` … `TE-6101` thermocouples | `TIC-0101` … `TIC-6101` | Heaters `-TH0101` … `-TH6101` |
| Barrel zones 0 to 6 cooling (7 manual commands) | – | `HS-0101` … `HS-6101` hand switches | Fans `-F0101` … `-F6101` |
| Melt pressure after the filter | `PT-0101` | `PI-0101` | – |

Equipment without instruments of its own: main extruder motor `-ME0101`, cooling water pump `-B0101`, hopper, melt filter.

## Symbol count (generated, revision 4)

Counted by intercepting the generator's `bubble()` and `plc()` calls, without the two legend samples:

| | Discrete instrument circles | Controller / screen functions (diamond in square) | Total |
|---|---:|---:|---:|
| Area 02 (spinning) | 14 | 26 | 40 |
| Area 01 (extruder) | 8 | 15 | 23 |
| **Sheet** | **22** | **41** | **63** |

Speed references, start/stop commands and bus values of the four roll drives are written as labels next to each drive rather than drawn as separate symbols, so they are not in this count.
