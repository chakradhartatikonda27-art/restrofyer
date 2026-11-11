"use client";

import { useEffect, useState } from "react";
import { Sun, Moon, Monitor } from "lucide-react";
import {
  ThemePreference,
  ResolvedTheme,
  getStoredThemePreference,
  getSystemTheme,
  applyThemePreference,
  toggleThemeScheme,
  syncMetaFromStorage,
} from "@/lib/theme";

/**
 * Compact header toggle following two-state color-scheme semantics (CSS-driven icons/SR text).
 */
export function ThemeToggle({ className = "" }: { className?: string }) {
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === null || e.key === "color-scheme") {
        syncMetaFromStorage();
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  return (
    <button
      type="button"
      onClick={() => toggleThemeScheme()}
      title="Switch color theme (White / Dark)"
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-line bg-panel hover:bg-control text-ink-3 hover:text-ink text-xs font-semibold shadow-sm transition ${className}`}
    >
      <span className="theme-when-dark items-center gap-1.5">
        <Sun className="w-3.5 h-3.5 text-amber-400" aria-hidden="true" />
        <span>White</span>
        <span className="sr-only">Switch to white light theme</span>
      </span>
      <span className="theme-when-light items-center gap-1.5">
        <Moon className="w-3.5 h-3.5 text-slate-600" aria-hidden="true" />
        <span>Dark</span>
        <span className="sr-only">Switch to dark theme</span>
      </span>
    </button>
  );
}

/**
 * Explicit three-state Appearance selector for Settings surfaces (System / Light / Dark).
 */
export function ThemePreferenceSelector() {
  const [preference, setPreference] = useState<ThemePreference>("system");
  const [systemTheme, setSystemTheme] = useState<ResolvedTheme>("light");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setPreference(getStoredThemePreference());
    setSystemTheme(getSystemTheme());

    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    const onSystemChange = (e: MediaQueryListEvent) => {
      // Only update display hint; do NOT overwrite or clear any saved preference
      setSystemTheme(e.matches ? "dark" : "light");
    };
    const onStorage = (e: StorageEvent) => {
      if (e.key === null || e.key === "color-scheme") {
        setPreference(syncMetaFromStorage());
      }
    };

    mql.addEventListener("change", onSystemChange);
    window.addEventListener("storage", onStorage);
    return () => {
      mql.removeEventListener("change", onSystemChange);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  const handleSelect = (next: ThemePreference) => {
    setPreference(next);
    applyThemePreference(next);
  };

  const options: {
    id: ThemePreference;
    label: string;
    description: string;
    icon: typeof Monitor;
  }[] = [
    {
      id: "system",
      label: mounted
        ? `System (Currently ${systemTheme})`
        : "System Default",
      description: "Follows your OS appearance setting automatically",
      icon: Monitor,
    },
    {
      id: "light",
      label: "White (Light Mode)",
      description: "Crisp white canvas for bright daylight & counter displays",
      icon: Sun,
    },
    {
      id: "dark",
      label: "Dark Mode",
      description: "Low-glare dark workspace for evening & bar service",
      icon: Moon,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3" role="radiogroup" aria-label="Interface Appearance Theme">
      {options.map((opt) => {
        const Icon = opt.icon;
        const selected = mounted && preference === opt.id;
        return (
          <button
            key={opt.id}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => handleSelect(opt.id)}
            className={`p-4 rounded-xl border text-left transition flex items-start gap-3 ${
              selected
                ? "bg-tint-brand border-tint-brand-border ring-1 ring-brand-500/40"
                : "bg-well border-line hover:bg-control"
            }`}
          >
            <div
              className={`p-2 rounded-lg shrink-0 ${
                selected ? "bg-brand-500 text-white" : "bg-control text-ink-muted"
              }`}
            >
              <Icon className="w-4 h-4" aria-hidden="true" />
            </div>
            <div>
              <div className={`text-xs font-bold ${selected ? "text-accent-brand" : "text-ink"}`}>
                {opt.label}
              </div>
              <div className="text-[11px] text-ink-muted mt-0.5 leading-snug">
                {opt.description}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
