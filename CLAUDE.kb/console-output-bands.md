# How addon output reaches the mitmproxy console (curses) UI

`proxy.sh` runs the **console** tool (`mitmproxy`, the curses TUI), not
`mitmdump`. Under it, `print(..., file=sys.stderr)` is wrong: the TUI owns
the terminal, so raw stderr **corrupts the display** and lands in no log
pane. The supported channel is the stdlib **`logging`** module — mitmproxy
installs a root-logger handler (`MitmLogHandler`) and routes records into its
UI. The same calls fall back to stderr under CLI tools (e.g.
`check_patches.py`), so one `logging` call serves both runtimes.

## Output surfaces (the "bands")

Three UI surfaces, selected by log **level**:

| Surface | Shows | Source |
| --- | --- | --- |
| Event-log pane (toggle `E`) | everything ≥ `console_eventlog_verbosity` | `console/eventlog.py:add_event` |
| Status bar (bottom, ~5s flash) | **only `error` / `warn` / `alert`**, prefixed `Error:`/`Warn:`/`Alert:` | `console/master.py:sig_add_log` |
| flow list / flowview | per-flow, not a logging band | — |

## Levels

| stdlib level | tier | color | status-bar flash |
| --- | --- | --- | --- |
| `ERROR` | error | red | yes (+ error semantics) |
| `WARNING` | warn | yellow | yes |
| `ALERT` (`mitmproxy.log.ALERT` = `INFO+1`) | alert | magenta | yes, but info-urgency |
| `INFO` | info | plain | no (event log only) |
| `DEBUG` | debug | plain | no (hidden unless verbosity raised) |

`ALERT` is the "draw attention without crying error" band, but using it adds a
real `mitmproxy` import to an otherwise standalone module.

## Convention in this repo

`prompt_patches.py` patch-failure reporting:

- failure headline → `logging.warning(...)` (event log + status-bar flash)
- `saved offending body -> …` breadcrumb → `logging.info(...)` (event log only)

Grounded in mitmproxy 12.2.1 source.
