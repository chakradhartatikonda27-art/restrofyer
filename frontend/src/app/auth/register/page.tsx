"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Building2, User, Mail, Lock, Phone, ArrowRight } from "lucide-react";
import { apiRequest } from "@/lib/api";
import { saveAuthSession } from "@/lib/auth";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function RegisterTenantPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    restaurant_name: "",
    owner_name: "",
    email: "",
    password: "",
    phone: "",
    business_type: "Casual Dining",
    country: "India",
    currency: "INR",
    plan_code: "growth"
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await apiRequest("/auth/register", {
        method: "POST",
        body: JSON.stringify(formData),
      });

      localStorage.setItem("saas_auth_token", res.access_token);
      const profile = await apiRequest("/auth/me");
      saveAuthSession(res.access_token, profile);

      router.push("/onboarding");
    } catch (err: any) {
      setError(err.message || "Failed to register tenant");
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
        <h2 className="text-2xl font-bold tracking-tight text-ink">Start your 14-day restaurant trial</h2>
        <p className="mt-2 text-sm text-ink-muted">
          Already have an account?{" "}
          <Link href="/auth/login" className="font-medium text-accent-brand hover:underline">
            Sign in
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-lg">
        <div className="bg-panel border border-line py-8 px-6 shadow-xl rounded-2xl sm:px-10">
          {error && (
            <div className="mb-6 p-3 rounded-lg bg-tint-rose border border-tint-rose-border text-accent-red text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Restaurant Organization Name</label>
              <div className="relative">
                <Building2 className="w-4 h-4 text-ink-subtle absolute left-3 top-2.5 pointer-events-none" />
                <input
                  type="text"
                  required
                  value={formData.restaurant_name}
                  onChange={(e) => setFormData({ ...formData, restaurant_name: e.target.value })}
                  placeholder="e.g. Saffron Bistro & Lounge"
                  className="w-full pl-9 pr-3 py-2 bg-well border border-input-border rounded-lg text-ink text-sm focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">Owner Name</label>
                <div className="relative">
                  <User className="w-4 h-4 text-ink-subtle absolute left-3 top-2.5 pointer-events-none" />
                  <input
                    type="text"
                    required
                    value={formData.owner_name}
                    onChange={(e) => setFormData({ ...formData, owner_name: e.target.value })}
                    placeholder="e.g. John Doe"
                    className="w-full pl-9 pr-3 py-2 bg-well border border-input-border rounded-lg text-ink text-sm focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">Phone Number</label>
                <div className="relative">
                  <Phone className="w-4 h-4 text-ink-subtle absolute left-3 top-2.5 pointer-events-none" />
                  <input
                    type="tel"
                    required
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="+91 98765 43210"
                    className="w-full pl-9 pr-3 py-2 bg-well border border-input-border rounded-lg text-ink text-sm focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Business Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-ink-subtle absolute left-3 top-2.5 pointer-events-none" />
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="owner@restaurant.com"
                  className="w-full pl-9 pr-3 py-2 bg-well border border-input-border rounded-lg text-ink text-sm focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-3 mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-ink-subtle absolute left-3 top-2.5 pointer-events-none" />
                <input
                  type="password"
                  required
                  minLength={6}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="Min 6 characters"
                  className="w-full pl-9 pr-3 py-2 bg-well border border-input-border rounded-lg text-ink text-sm focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">Business Concept</label>
                <select
                  value={formData.business_type}
                  onChange={(e) => setFormData({ ...formData, business_type: e.target.value })}
                  className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-ink text-sm focus:ring-2 focus:ring-brand-500"
                >
                  <option value="Fine Dining">Fine Dining</option>
                  <option value="Casual Dining">Casual Dining</option>
                  <option value="Cafe & Bakery">Cafe & Bakery</option>
                  <option value="Quick Service / QSR">Quick Service / QSR</option>
                  <option value="Bar & Pizzeria">Bar & Pizzeria</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">Trial Plan</label>
                <select
                  value={formData.plan_code}
                  onChange={(e) => setFormData({ ...formData, plan_code: e.target.value })}
                  className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-ink text-sm focus:ring-2 focus:ring-brand-500"
                >
                  <option value="starter">Starter (1 Branch)</option>
                  <option value="growth">Growth (3 Branches)</option>
                  <option value="pro">Professional (10 Branches)</option>
                  <option value="enterprise">Enterprise</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-4 flex justify-center items-center gap-2 py-2.5 px-4 rounded-lg text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 transition disabled:opacity-50"
            >
              {loading ? "Creating Tenant Workspace..." : "Create Restaurant Account"}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
