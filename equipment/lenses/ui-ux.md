# UI/UX Lens

## When to Equip

Use when reviewing frontend components, user-facing flows, HTML templates,
form handling, navigation, or any code that affects what users see and interact with.

## Focus Areas

- [ ] Semantic HTML - proper landmarks, headings hierarchy, native elements
- [ ] ARIA labels and roles - all interactive elements have accessible names
- [ ] Keyboard navigation - all interactive elements focusable via keyboard
- [ ] Focus management - logical focus order, focus traps in modals
- [ ] Color contrast - WCAG 2.1 AA minimum (4.5:1 normal, 3:1 large text)
- [ ] Loading states - spinners or skeletons for async operations
- [ ] Error handling UX - clear error messages near relevant field
- [ ] Empty states - meaningful messaging when no data is present
- [ ] Form validation feedback - inline validation, success/error indicators
- [ ] Responsive design - layouts adapt across breakpoints, touch targets >= 44px
- [ ] Design system consistency - uses design tokens, no hardcoded values
- [ ] Destructive actions - irreversible operations have confirmation dialogs
- [ ] Motion and animation - respect `prefers-reduced-motion`

## Patterns to Flag

- Missing `alt` text on images
- Missing ARIA labels on interactive elements
- Non-semantic HTML - `<div>` where `<button>`, `<nav>`, `<main>` belong
- Missing focus indicators
- Color as sole means of conveying information
- Silent failures - errors swallowed without user feedback
- Form inputs without associated `<label>` or `aria-label`
- Yellow/orange text without verified contrast ratios

## Reference

- WCAG 2.1 AA
- WAI-ARIA Authoring Practices
- Nielsen's 10 Usability Heuristics
