export type ThemePreference = "system" | "light" | "dark";
export type ResolvedTheme = "light" | "dark";

const STORAGE_KEY = "color-scheme";

function getColorSchemeMeta(): HTMLMetaElement | null {
  if (typeof document === "undefined") return null;
  return document.querySelector('meta[name="color-scheme"]');
}

/**
 * Returns the OS/browser's current preferred color scheme.
 */
export function getSystemTheme(): ResolvedTheme {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

/**
 * Reads the persisted theme override ("light" | "dark") or returns "system".
 */
export function getStoredThemePreference(): ThemePreference {
  if (typeof window === "undefined") return "system";
  try {
    const val = window.localStorage.getItem(STORAGE_KEY);
    if (val === "light" || val === "dark") return val;
  } catch {
    // Ignore storage access errors in restricted privacy contexts
  }
  return "system";
}

/**
 * Computes the effective scheme currently rendered on the document.
 */
export function getResolvedTheme(): ResolvedTheme {
  const stored = getStoredThemePreference();
  if (stored === "light" || stored === "dark") return stored;
  return getSystemTheme();
}

/**
 * Synchronizes <meta name="color-scheme"> with stored or system preference.
 */
export function applyThemePreference(pref: ThemePreference): void {
  if (typeof window !== "undefined") {
    try {
      if (pref === "system") {
        window.localStorage.removeItem(STORAGE_KEY);
      } else {
        window.localStorage.setItem(STORAGE_KEY, pref);
      }
    } catch {
      // Theme still applies to current view even if persistence is blocked
    }
  }
  const meta = getColorSchemeMeta();
  if (meta) {
    meta.content = pref === "system" ? "light dark" : pref;
  }
}

/**
 * Applies the two-state toggle semantics: switches to the opposite of the currently
 * rendered scheme, storing only when it diverges from the system preference.
 */
export function toggleThemeScheme(): ThemePreference {
  const currentRendered = getResolvedTheme();
  const target: ResolvedTheme = currentRendered === "dark" ? "light" : "dark";
  const system = getSystemTheme();
  const nextPref: ThemePreference = target === system ? "system" : target;
  applyThemePreference(nextPref);
  return nextPref;
}

/**
 * Syncs <meta name="color-scheme"> when another browser tab updates storage.
 */
export function syncMetaFromStorage(): ThemePreference {
  const pref = getStoredThemePreference();
  const meta = getColorSchemeMeta();
  if (meta) {
    meta.content = pref === "system" ? "light dark" : pref;
  }
  return pref;
}
