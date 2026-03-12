"use client";

import { useEffect, useSyncExternalStore, type ReactNode } from "react";

export interface HeaderBackOverride {
  label: string;
  href: string;
}

// Module-level store so Header (sibling in the tree) can read values
// set by page components (children in the tree).
let _current: HeaderBackOverride | null = null;
const _listeners = new Set<() => void>();

function subscribe(cb: () => void) {
  _listeners.add(cb);
  return () => _listeners.delete(cb);
}

function getSnapshot() {
  return _current;
}

export function setHeaderBack(value: HeaderBackOverride | null) {
  if (_current === value) return;
  _current = value;
  _listeners.forEach((cb) => cb());
}

export function useHeaderBack(): HeaderBackOverride | null {
  return useSyncExternalStore(subscribe, getSnapshot, () => null);
}

/**
 * Renders children and sets the header back override while mounted.
 * Works across the component tree (not limited to React context nesting).
 */
export function HeaderBackProvider({
  label,
  href,
  children,
}: HeaderBackOverride & { children: ReactNode }) {
  useEffect(() => {
    setHeaderBack({ label, href });
    return () => setHeaderBack(null);
  }, [label, href]);

  return <>{children}</>;
}
