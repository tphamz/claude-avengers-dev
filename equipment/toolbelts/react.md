# React Toolbelt

## When to Equip

Use when implementing or modifying React components, hooks, state management,
or frontend features in a React/Next.js project.

## Folder Structure

When the project has no established layout:

- `src/features/<feature>/`: components, hooks, API calls and tests for one feature
- `src/components/`: shared components used by more than one feature
- `src/hooks/`: shared hooks used by more than one feature
- `app/`: Next.js only; routes and layouts, which import domain code from `src/features/`

## Conventions

- **Functional components only** - no class components
- **Hooks for state and effects** - useState, useEffect, useCallback, useMemo, useRef
- **One component per file**, named export matching filename
- **TypeScript interfaces** for all component props
- **Colocation**: tests, styles, types alongside their component

## Implementation Patterns

- [ ] `useState` for local state, context/library for shared state
- [ ] `useMemo` for expensive computations with correct dependency arrays
- [ ] `useCallback` for callback props to prevent child re-renders
- [ ] Cleanup functions from `useEffect` for subscriptions and timers
- [ ] Controlled components for form inputs
- [ ] Handle loading, error, and empty states explicitly

## Testing Patterns

- React Testing Library - not Enzyme
- Query by role, label, text - not class or test ID
- `userEvent` over `fireEvent`
- `waitFor` or `findBy` for async operations
- MSW for API mocking

## Patterns to Avoid

- Direct DOM manipulation - use refs instead
- Derived state in useState
- Object/array literals in JSX props (new reference every render)
- Index as key for lists that can reorder, insert, or delete
- useEffect for data that can be computed during render
- Long `if`/`switch` chains on a type or kind to choose what to render - use a lookup map from kind to component
