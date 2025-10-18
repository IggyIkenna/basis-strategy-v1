Love it—let’s give this a polished, “institutional” vibe.

I’ve dropped a **drop-in replacement** for your Share Class step into the canvas: a clean, dark-mode friendly, shadcn/Tailwind page with proper hierarchy, badges, subtle motion, and accessible radio-card behavior. It uses your existing stack (React + TS + Tailwind + shadcn + lucide + Framer Motion).

### How to use

* Put the component in your frontend (e.g. `frontend/src/components/wizard/InstitutionalShareClassStep.tsx`).
* Replace your current ShareClass step with the new default export.
* Props:

  * `selected?: "USDT" | "ETH"`
  * `onSelect(share: ShareClass)`
  * `onNext()`
  * `onBack?()`

### Design notes (institutional polish)

* **Hierarchy & density**: bigger headline, softer subcopy, compact bullet rows with icons.
* **Professional color system**: neutral slate + emerald accent; subtle gradients only in the header.
* **A11y**: cards behave like radios (`role="radio"`, `aria-checked`, keyboard select with Enter/Space).
* **Dark mode**: fully styled for `dark:` tokens.
* **Micro-interactions**: tasteful hover/selection ring, slight icon motion on Continue.

### Next quick wins (I can wire these next)

1. **Wizard shell** with sticky stepper + page title bar (breadcrumb + step number).
2. **Institutional card kit**: `KPIStat`, `Section`, `InfoStrip`, `RiskBadge`.
3. **Results header**: compact KPI band (PnL / APY / Sharpe / DD) with export buttons.
4. **Typography pass**: tighten letter/line-height and consistent numerals for metrics.

If you want, I’ll style the **Mode selection** grid similarly (risk chips, APY mini-stack, concise blurbs, consistent cards) and give the Results Overview the same treatment.
