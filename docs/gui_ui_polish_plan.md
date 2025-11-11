# ClickClick GUI Polish and UX Plan

This plan outlines incremental, testable changes to improve the Tkinter GUI in `src/gui_window.py`. Each section includes scope, implementation details, and acceptance criteria so we can land changes in small PRs.

## 0. Foundations

- Central Theme class
  - Create `Theme` dataclass to centralize palette, spacing, and fonts.
  - Provide helpers: `hex_lerp(a, b, t)`, `apply_window_bg(root)`, spacing constants (4, 8, 12, 16).
  - Wire `ttk.Style` variants: `Header.TFrame`, `Card.TFrame`, `Primary.TButton`, `Danger.TButton`, `Muted.TLabel`, `Pill.TLabel`.
  - Acceptance: All widgets use style names; no hardcoded hexes outside Theme except Canvas draws.

- High‑DPI scaling
  - On Windows, set DPI awareness via `ctypes.windll.shcore.SetProcessDpiAwareness(1)` (best‑effort, guard with try/except).
  - Configure Tk scaling: `root.tk.call('tk', 'scaling', dpi/96)` or fixed 1.25 as fallback.
  - Acceptance: Text and icons appear crisp; no layout clipping at common scaling.

- Debounce + UI event bridge
  - Debounce helper: keyed timers stored on `GUIWindow`, `debounce(key, ms, func, *args)`. Cancels prior `after` before scheduling new.
  - Thread‑safe UI bridge: `queue.Queue()` for backend → UI events; poll with `after(30)` to update labels and state.
  - Acceptance: No flicker in status/position updates; handlers not called excessively.

## 1. Header Bar (Modern)

- Add a top header card with:
  - App title "ClickClick!", optional version, small status pill (Idle/Running).
  - Optional window icon on the left.
- Styles
  - `Header.TFrame` background, larger font for title, `Pill.TLabel` for status with color mapping (green for Running, slate for Idle).
- Behavior
  - Status pill animates color on state change (use `animate_color` helper with `after`).
  - Optional translucency boost when idle.
- Acceptance: Distinct top section; status pill updates on start/stop.

## 2. Card Layout

- Group controls into titled cards:
  - Timing (min/max delay + Apply)
  - Offset (scale + live value)
  - Behavior (Always‑on‑top, Show indicator, Console output)
  - Hotkey (capture/clear)
- Use `Card.TFrame` with consistent padding and grid spacing.
- Acceptance: Visual grouping with consistent 12–16px padding; no overlapping; keyboard traversal intact.

## 3. Iconography

- Window icon and inline icons for buttons/toggles.
- Use small PNGs or emoji fallback; create `IconRegistry` to load/cached `PhotoImage` at 1x/1.25x depending on scaling.
- Keep consistent sizing (16px, 20px where appropriate) and left padding.
- Acceptance: Icons render crisp; buttons align text + icon properly.

## 4. Status Styling on Start/Stop

- `Start/Stop` button uses style swap:
  - Idle: `Primary.TButton` (accent background)
  - Running: `Danger.TButton` (danger background)
- Add hover/active maps via `Style.map` for both styles.
- Acceptance: Visual distinction between states; hover feedback present.

## 5. Translucency

- Window alpha set to ~0.96 when idle; restore 1.0 on hover or when running.
- Guard with platform checks; avoid while fullscreen apps detected (best‑effort, optional later).
- Acceptance: Subtle translucency visible when idle; no readability issues.

## 6. Decimal Delays + Spinbox

- Switch `min_delay_var`/`max_delay_var` to `tk.DoubleVar`.
- Replace Entry fields with `ttk.Spinbox` (`from_=0.1`, `to=10.0`, `increment=0.1`, `format='%.1f'`).
- Validate that `min ≤ max` and both within bounds; show inline error banner (see Section 9) after debounce of ~200ms.
- Acceptance: Inputs clamp to bounds, precise increments, no flicker.

## 7. Scale Affordance (Offset)

- Show live numeric value label aligned to the right of the scale.
- Colorize the value as it changes (interpolate neutral → highlight based on magnitude).
- Acceptance: Offset changes feel responsive; value always visible and readable.

## 8. Non‑Blocking Updates

- Move any background updates (position, applied delay) onto the UI bridge queue.
- Ensure backend threads never call Tk directly; they enqueue messages.
- Acceptance: No cross‑thread Tk calls; smooth updates at 30–60Hz.

## 9. Error Banner + Toasts

- Error banner
  - Dismissible colored banner at top of the window/card for validation errors.
  - Auto‑hide after N seconds; supports multiple messages with last‑one‑wins.
- Toast notifications
  - Lightweight `Toplevel` with `overrideredirect(True)`; fade in/out using alpha steps.
  - Used for confirmations: "Settings saved", "Hotkey set to …".
- Acceptance: Clear, non‑intrusive feedback; no persistent overlays.

## 10. Running Indicator with Countdown Overlay

- Keep red/green indicator; add accurate countdown overlay to next click.
- Implementation options:
  1) Canvas circular arc that fills based on remaining time / interval.
  2) Small `ttk.Progressbar` overlaid; text label shows `X.Ys`.
- Backend → UI event includes next scheduled click timestamp or remaining seconds; UI computes remaining via `after(33)` tick.
- Acceptance: Countdown updates smoothly; matches actual next click timing within ~50ms.

## 11. Style Maps and Animation Helpers

- Style maps for hover/active/disabled states on `TButton`, `TCheckbutton`, `TScale`.
- `animate_color(widget, from_hex, to_hex, duration_ms, apply_fn)` utility using `after` + `hex_lerp`.
- Acceptance: Subtle transitions on state changes (header pill, start/stop, offset label).

## 12. Persistence + Confirmation

- Settings JSON save triggers toast "Settings saved".
- Also persist last indicator position and window geometry (optional in later pass).
- Acceptance: Confirmation toast appears; settings file contains updated values.

---

## Milestones and PR Breakdown

1) Foundations: Theme, DPI scaling, debounce, UI bridge. Low risk. Touchpoints: `GUIWindow.__init__`, helpers module or inner class.
2) Header Bar + Style Maps: Visual upgrade, status pill, start/stop maps.
3) Card Layout + Spinboxes + Decimal Delays: UX correctness for timing inputs.
4) Offset Affordance + Non‑Blocking Updates: Smoothness and readability.
5) Running Indicator Countdown + Translucency: Visual and functional polish.
6) Iconography + Toasts + Error Banner: Feedback and finish.

Each milestone should keep app runnable; feature flags can be temporary via simple booleans if needed.

## File‑Level Changes (anticipated)

- src/gui_window.py
  - Add `Theme` class and style setup.
  - Introduce debounce helper and event queue.
  - Replace delay entries with `ttk.Spinbox` and `DoubleVar`.
  - Header bar widgets and card frames.
  - Running indicator with countdown (Canvas overlay or Progressbar).
  - Translucency control and toasts.

- assets/
  - Optional: 16–20px PNG icons; fallback to emoji if unavailable.

## Testing and Validation

- Manual checks
  - Toggle start/stop multiple times; confirm style switches and animations.
  - Enter invalid delays quickly; error banner appears after debounce, disappears on fix.
  - Move offset; value color updates smoothly.
  - Observe countdown accuracy vs backend interval.
  - Save settings; toast confirmation appears.

- Performance
  - Keep UI tick <= 33ms; avoid long‑running handlers.
  - Ensure no Tk calls from threads; only via main loop.

## Rollback / Safety

- All changes guarded by local helpers and styles; can revert header/animations independently.
- Fallbacks for missing packages (e.g., no hotkey capture) remain unchanged.

