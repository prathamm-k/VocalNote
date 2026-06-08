# VocalNote — UI Design System

> **वोकलनोट** — *Vaak* (वाक्) means "speech/voice" in Sanskrit.

## Design Philosophy

This UI draws from **contemporary Indian aesthetics** — specifically:

- **Jaipur blue pottery** patterns as subtle background textures
- **Mughal arch** shapes for feature card top-corners
- **Mandala** geometry for loading spinners and decorative watermarks
- **Diya lamp** metaphors for status indicators (the flame flickers during processing)
- **Rangoli** patterns as section dividers (gold gradient lines with glowing dots)
- **Peacock feather** shimmer effects on hover states

---

## Design Tokens

### Color Palette

| Token | Hex | Usage |
|---|---|---|
| `--saffron` | `#FF9933` | Primary CTA, accents, text highlights |
| `--indian-green` | `#138808` | Success states, status indicators |
| `--navy-chakra` | `#000080` | Deep accent (used sparingly) |
| `--gold-foil` | `#D4AF37` | Shimmer text, divider glows, borders |
| `--terra-cotta` | `#C2703E` | Button gradients, warm accents |
| `--turmeric` | `#D4A843` | Gold text gradient component |
| `--rosewood` | `#65000B` | Deep accent, diya lamp body |
| `--pomegranate` | `#C62828` | Error states |
| `--bg-primary` | `#1a1028` | Page background (warm dark purple) |
| `--bg-card` | `#2a1e3d` | Card backgrounds |
| `--ivory-warm` | `#FFF8EE` | Light mode text (unused, reserved) |

### Typography

| Role | Font Family | Weight | Notes |
|---|---|---|---|
| Display/Headlines | Poppins | 700–800 | Wide letter-spacing, gold shimmer on brand |
| Body text | Inter | 400–600 | Line-height 1.75 for outdoor readability |
| Devanagari accents | Tiro Devanagari Hindi | 400 | Decorative section labels (e.g., "पॉडकास्ट जनरेटर") |

### Motion

| Token | Value | Inspiration |
|---|---|---|
| `--ease-mudra` | `cubic-bezier(0.4, 0, 0.2, 1)` | Fluid like classical dance hand gestures |
| `--duration-base` | `0.35s` | Primary transition duration |
| `--duration-gentle` | `0.8s` | Page entrance animations |
| `goldShimmer` | 6s loop | Gold foil text gradient animation |
| `diyaPulse` | 3s loop | Glowing diya lamp status indicator |
| `flameFlicker` | 0.8s alternate | Processing state flame animation |
| `mandalaRotate` | 120s linear | Background mandala slow rotation |

---

## Component Architecture

```
src/
├── index.css              # Design tokens, reset, global utilities
├── App.tsx                # Main app (state + API logic preserved)
├── App.css                # Layout + background patterns
├── components/
│   ├── Header.tsx/.css    # Sticky glassmorphism header + diya brand icon
│   ├── HeroUpload.tsx/.css # Upload zone + mandala decorations + CTA
│   ├── StatusBar.tsx/.css  # Processing diya flame / success / error states
│   ├── AudioPlayer.tsx/.css# Custom player with waveform + seek slider
│   ├── FeatureCards.tsx/.css# 3-step pipeline cards with Mughal arch tops
│   └── Footer.tsx/.css    # Tech badges + rangoli divider
├── assets/
│   └── patterns/
│       ├── mandala.svg    # Mandala watermark
│       ├── paisley.svg    # Paisley texture
│       └── jaipur-tile.svg# Jaipur pottery tile
```

---

## API Integration

All API calls are in `App.tsx` and remain **unchanged** from the original:

```typescript
// POST /generate-podcast — sends PDF as multipart/form-data, expects WAV blob
const response = await axios.post('http://localhost:9000/generate-podcast', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
  responseType: 'blob',
});
```

**To swap the backend URL**, change the URL string in `App.tsx` line ~44. No other files reference the backend.

---

## Accessibility

- **Focus states**: 2px saffron outline on `:focus-visible`
- **Touch targets**: All buttons ≥ 44×44px
- **High contrast**: `@media (prefers-contrast: high)` overrides tokens
- **Screen reader**: `sr-only` class for labels, `aria-label` on interactive elements
- **Motion**: Animations use `prefers-reduced-motion` (respects system setting via CSS)

---

## Running Locally

```bash
cd frontend
npm install
npm run dev    # → http://localhost:2000
```

Backend must be running at `http://localhost:9000`.
