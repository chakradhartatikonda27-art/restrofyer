"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Lock, Mail, ArrowRight } from "lucide-react";
import { apiRequest } from "@/lib/api";
import { saveAuthSession } from "@/lib/auth";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("owner@spicesymphony.com");
  const [password, setPassword] = useState("Owner@456");
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const endpoint = isSuperAdmin ? "/auth/platform-login" : "/auth/login";
      const res = await apiRequest(endpoint, {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      localStorage.setItem("saas_auth_token", res.access_token);
      const profile = await apiRequest("/auth/me");
      saveAuthSession(res.access_token, profile);

      if (isSuperAdmin) {
        router.push("/platform");
      } else {
        router.push("/app/dashboard");
      }
    } catch (err: any) {
      setError(err.message || "Failed to authenticate");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-canvas flex flex-col justify-center py-12 px-6 sm:px-8 relative">
      <div className="absolute top-6 right-6">
        <ThemeToggle />
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link href="/" className="inline-flex items-center gap-2 mb-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-amber-400 flex items-center justify-center shadow-lg shadow-brand-500/20 text-white font-bold text-xl">
            R
          </div>
          <span className="font-extrabold text-2xl tracking-tight text-ink">Resto<span className="text-brand-600">SaaS</span></span>
        </Link>
        <h2 className="text-2xl font-bold tracking-tight text-ink">Sign in to your restaurant workspace</h2>
        <p className="mt-2 text-sm text-ink-muted">
          Or{" "}
          <Link href="/auth/register" className="font-medium text-accent-brand hover:underline">
            register a new restaurant tenant
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-panel border border-line py-8 px-6 shadow-xl rounded-2xl sm:px-10">
          {error && (
            <div className="mb-6 p-3 rounded-lg bg-tint-rose border border-tint-rose-border text-accent-red text-sm">
              {error}
            </div>
          )}

          <div className="flex rounded-xl bg-well p-1 mb-6 border border-line">
            <button
              type="button"
              onClick={() => { setIsSuperAdmin(false); setEmail("owner@spicesymphony.com"); setPassword("Owner@456"); }}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition ${
                !isSuperAdmin ? "bg-brand-600 text-white shadow" : "text-ink-muted hover:text-ink"
              }`}
            >
              Restaurant Staff
            </button>
            <button
              type="button"
              onClick={() => { setIsSuperAdmin(true); setEmail("admin@restaurantsaas.com"); setPassword("SuperAdmin@2026!"); }}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition ${
                isSuperAdmin ? "bg-amber-500 text-slate-950 font-bold shadow" : "text-ink-muted hover:text-ink"
              }`}
            >
              Platform Super Admin
            </button>
          </div>

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1.5">
                Work Email Address
              </label>
              <div className="relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-ink-subtle">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-9 pr-3 py-2 bg-well border border-input-border rounded-lg text-ink placeholder:text-ink-subtle text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  placeholder="you@restaurant.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1.5">
                Password
              </label>
              <div className="relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-ink-subtle">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-9 pr-3 py-2 bg-well border border-input-border rounded-lg text-ink placeholder:text-ink-subtle text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center gap-2 py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 transition disabled:opacity-50"
            >
              {loading ? "Authenticating..." : "Sign In"}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Credential Hints */}
          <div className="mt-6 pt-6 border-t border-line text-xs text-ink-subtle space-y-1">
            <div className="font-semibold text-ink-muted">Demo Credentials:</div>
            <div>Tenant Owner: <span className="text-ink-3 font-mono">marco@bellanapoli.com</span> / <span className="text-ink-3 font-mono">Owner@123</span></div>
            <div>Cashier (POS): <span className="text-ink-3 font-mono">lucas@bellanapoli.com</span> / <span className="text-ink-3 font-mono">Cashier@123</span></div>
            <div>Super Admin: <span className="text-ink-3 font-mono">admin@restaurantsaas.com</span> / <span className="text-ink-3 font-mono">SuperAdmin@2026!</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}
