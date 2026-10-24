# How to read the tags and symbols in this P&ID

This is a short guide, written for this repository, to the conventions used in the drawing. It follows the ideas of ANSI/ISA-5.1-2009 *Instrumentation Symbols and Identification*. The standard itself is copyrighted and is not included here; get it from ISA if you need the exact tables.

## 1. Anatomy of a tag

An instrument tag has two parts:

```
   P  T  B  -  0 3
   |  |__|     |__|
   |    |        +-- loop number: every device in the same loop shares it
   |    +----------- succeeding letters: what the device does
   +---------------- first letter: the variable being measured or initiated
```

- **First letter = measured or initiating variable.** It says *what* is measured, not what the device is. A temperature switch starts with T, not S.
- **Succeeding letters = functions**, read in a fixed order: passive or readout functions (element, indicator, glass, record), then output functions (controller, switch, relay, valve), then modifiers (high, low).
- **Loop number.** The field sensor, the controller and the final element of one loop share the number, so `TE-0101` (thermocouple) and `TIC-0101` (temperature indicating controller) belong together.

Letters used in this drawing:

| Letter | As first letter (variable) | As succeeding letter (function or modifier) |
|---|---|---|
| P | Pressure | – |
| T | Temperature | Transmitter |
| S | Speed | Switch / status |
| L | Level | Low |
| M | Moisture (humidity) | – |
| Z | Position | – |
| H | Hand (manual) | High |
| X | Unclassified (used here for drive run and fault states) | – |
| N | User's choice (used by the course signal list for start/stop and contactor commands) | – |
| E | – | Primary element (sensor) |
| I | – | Indicate |
| C | – | Control |
| A | – | Alarm |
| Y | – | Relay / compute / convert |

Examples from the drawing:

| Tag | Read as |
|---|---|
| `TE-0101` → `TIC-0101` | Temperature element in heating zone 0 of the extruder, read by a temperature indicating controller that drives the zone heater |
| `PT-0101` → `PI-0101` | Pressure transmitter after the melt filter, shown as a pressure indication |
| `PTB-03` → `PIA-03` | Melt pressure transmitter at spinneret 1, with indication and alarm in the controller (high alarm `PAH`) |
| `TEB-08` → `TI/TN-08` → `TY-07` | Thermal oil thermocouple, its display and set point on the screen, and the relay that switches the oil heaters |
| `LSL-02` → `MF-02` | Low level switch in the thermal oil tank, feeding a general alarm |
| `ZSB-14` | Position switch (limit switch) of the spin-finish tray |
| `MT-01` → `MI-01` | Proposed humidity transmitter at the quench air intake, with indication |

**Caveat.** The extruder tags (area 01) follow the format of the team that instrumented it (`TE-0101`, `-TH0101`, `-F0101`). The spinning-area tags (area 02) come from the signal list used in the course, which mixes ISA letters with plant-specific codes (`PTB`, `TEB`, `STD`, `SNM`, `XSR/XSF`, `NCD`). The drawing keeps those tags so it matches the controller signal list. They are not pure ISA-5.1.

## 2. Instrument symbols

| Symbol in the drawing | Meaning |
|---|---|
| Circle with tag letters and loop number | Discrete instrument (sensor or transmitter) |
| Square with an inscribed diamond | Function performed in a programmable logic controller (PLC) or shown on its operator screen |
| Circle with **M** | Electric motor |
| Rectangle labelled `VFD` | Variable frequency drive |
| Rectangle labelled `K` | Contactor or motor starter |
| Zigzag | Electric heater |
| Dome on a short line | Rupture disc (self-actuated pressure relief) |

A tag with `*` marks an assumed value or device that was not confirmed in the plant.

## 3. Lines

Every process service has its own layer, line pattern, colour and a two-letter code written in the line itself, so the sheet still reads correctly when plotted in black and white:

| Code | Service |
|---|---|
| FU | Polypropylene melt (main process, thick solid line) |
| – | Filaments and tow (double line) |
| AT | Thermal oil (spin beam heating) |
| AQ | Quench cooling air |
| HU | Fumes to extraction |
| EN | Spin-finish oil |
| AG | Cooling water |

Instrument connections use the ISA line types:

| Line | Meaning |
|---|---|
| Thin solid | Connection to the process, or power to a motor |
| Dashed | Electrical signal (4–20 mA analog or digital) |
| Solid line with small diamonds | Fieldbus or communication link (here, values read from a drive over its bus) |
| Solid line with a small circle | Mechanical link (motor shaft to pump, roll or fan) |
| Semicircle hop | Two lines that cross without connecting |

## 4. Areas and floors

- **Area 01** is the extruder, on floor 1. **Area 02** is the spinning area: the spin beam and quench rings on floor 2, and the finish and pulling rolls on floor 1.
- A double slash on the melt line marks the battery limit between the two areas.
- A long-dash line splits the sheet into the two floors.
