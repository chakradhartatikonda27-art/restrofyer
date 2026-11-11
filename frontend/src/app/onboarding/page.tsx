"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  CheckCircle2, MapPin, Receipt, Utensils,
  LayoutGrid, MonitorCheck, ArrowRight, ArrowLeft
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { ThemeToggle } from "@/components/ThemeToggle";

const DEFAULT_CUISINE_CHOICES = [
  "South Indian",
  "North Indian",
  "Andhra Special",
  "Telangana Special",
  "Kerala Special",
  "Tandoori",
  "Mughlai",
  "Chettinad",
  "Indo-Chinese",
  "Indian Street Food",
];

const DEFAULT_CATEGORY_CHOICES = [
  "Starters",
  "Soups",
  "Tiffins / Breakfast",
  "Main Course",
  "Meals / Thali",
  "Rice & Biryani",
  "Curries & Gravies",
  "Breads & Rotis",
  "Dosa & Idli",
  "Snacks",
  "Desserts",
  "Beverages",
  "Combos / Special Meals",
];

export default function OnboardingWizard() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Form states
  const [branchName, setBranchName] = useState("Downtown Flagship");
  const [branchCode, setBranchCode] = useState("MAIN-01");
  const [taxRate, setTaxRate] = useState(5.0);
  const [serviceCharge, setServiceCharge] = useState(0.0);

  const [selectedCuisines, setSelectedCuisines] = useState<string[]>([...DEFAULT_CUISINE_CHOICES]);
  const [categories, setCategories] = useState<string[]>([...DEFAULT_CATEGORY_CHOICES]);
  const [includeSampleDishes, setIncludeSampleDishes] = useState(true);
  const [newCat, setNewCat] = useState("");

  const [diningArea, setDiningArea] = useState("Main Dining Hall");
  const [tableCount, setTableCount] = useState(8);

  const [stations] = useState(["Grill & Oven", "Saute & Main", "Beverage & Dessert"]);

  const toggleCuisine = (c: string) => {
    setSelectedCuisines((prev) =>
      prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]
    );
  };

  const toggleCategory = (c: string) => {
    setCategories((prev) =>
      prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]
    );
  };

  const handleComplete = async () => {
    setLoading(true);
    try {
      const defaultSelected = categories.filter((c) => DEFAULT_CATEGORY_CHOICES.includes(c));
      const customCategories = categories.filter((c) => !DEFAULT_CATEGORY_CHOICES.includes(c));

      await apiRequest("/menus/templates/apply-indian-default", {
        method: "POST",
        body: JSON.stringify({
          cuisines: selectedCuisines,
          categories: defaultSelected,
          include_sample_dishes: includeSampleDishes,
          create_scheduled_menus: true,
        }),
      });

      for (let i = 0; i < customCategories.length; i++) {
        await apiRequest("/menus/categories", {
          method: "POST",
          body: JSON.stringify({
            name: customCategories[i],
            display_order: defaultSelected.length + i + 1,
          }),
        });
      }

      const area = await apiRequest("/tables/areas", {
        method: "POST",
        body: JSON.stringify({ name: diningArea, display_order: 1 })
      });

      for (let t = 1; t <= tableCount; t++) {
        await apiRequest("/tables", {
          method: "POST",
          body: JSON.stringify({
            area_id: area.id,
            table_number: `T-${t < 10 ? '0' : ''}${t}`,
            name: `Table ${t}`,
            capacity: t % 3 === 0 ? 6 : 4,
            pos_x: (t % 4) * 120 + 40,
            pos_y: Math.floor((t - 1) / 4) * 100 + 40
          })
        });
      }

      router.push("/app/dashboard");
    } catch (err: any) {
      alert(`Setup error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { num: 1, title: "Branch & Location", icon: MapPin },
    { num: 2, title: "Taxes & Currency", icon: Receipt },
    { num: 3, title: "Indian Menu Catalog", icon: Utensils },
    { num: 4, title: "Floor & Tables", icon: LayoutGrid },
    { num: 5, title: "Kitchen Routing", icon: MonitorCheck },
  ];

  return (
    <div className="min-h-screen bg-canvas text-ink-2 flex flex-col justify-center py-12 px-6 relative">
      <div className="absolute top-6 right-6">
        <ThemeToggle />
      </div>

      <div className="max-w-3xl mx-auto w-full">
        {/* Progress Header */}
        <div className="text-center mb-8">
          <div className="text-xs uppercase tracking-widest text-accent-brand font-bold">Restaurant Onboarding</div>
          <h1 className="text-2xl font-extrabold text-ink mt-1">Configure Your Operating Environment</h1>
          <p className="text-sm text-ink-muted mt-1">Step {step} of 5 — Takes less than 2 minutes</p>
        </div>

        {/* Step Indicator */}
        <div className="flex items-center justify-between mb-8 bg-panel border border-line p-4 rounded-xl shadow-sm">
          {steps.map((s, idx) => {
            const Icon = s.icon;
            const isCompleted = step > s.num;
            const isCurrent = step === s.num;
            return (
              <div key={s.num} className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold transition ${
                  isCompleted ? "bg-tint-emerald text-accent-emerald border border-tint-emerald-border" :
                  isCurrent ? "bg-brand-600 text-white shadow-lg shadow-brand-500/25" :
                  "bg-control text-ink-subtle border border-line"
                }`}>
                  {isCompleted ? <CheckCircle2 className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                </div>
                <span className={`text-xs font-medium hidden sm:inline ${isCurrent ? "text-ink font-semibold" : "text-ink-subtle"}`}>
                  {s.title}
                </span>
                {idx < steps.length - 1 && <div className="w-4 h-[1px] bg-line hidden md:block" />}
              </div>
            );
          })}
        </div>

        {/* Card Body */}
        <div className="bg-panel border border-line rounded-2xl p-8 shadow-xl">
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-ink">Your First Branch / Location</h2>
              <p className="text-xs text-ink-muted">Configure your primary location where POS terminals and dining rooms operate.</p>
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">Branch Name</label>
                <input
                  type="text"
                  value={branchName}
                  onChange={(e) => setBranchName(e.target.value)}
                  className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-sm text-ink"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">Branch Internal Code</label>
                <input
                  type="text"
                  value={branchCode}
                  onChange={(e) => setBranchCode(e.target.value)}
                  className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-sm text-ink"
                />
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-ink">Tax & Service Charges</h2>
              <p className="text-xs text-ink-muted">Configure applicable GST/VAT and optional hospitality service charges.</p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-ink-3 mb-1">Tax Rate (GST / VAT %)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={taxRate}
                    onChange={(e) => setTaxRate(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-sm text-ink"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-3 mb-1">Service Charge (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={serviceCharge}
                    onChange={(e) => setServiceCharge(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-sm text-ink"
                  />
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <div>
                <h2 className="text-lg font-bold text-ink">Indian Restaurant Menu Template</h2>
                <p className="text-xs text-ink-muted mt-0.5">
                  Cuisines and Dish Categories are stored independently (never mixed with Veg / Non-Veg / Egg / Vegan). Toggle or customize your defaults below.
                </p>
              </div>

              <div>
                <p className="text-[11px] font-bold uppercase tracking-wider text-ink-muted mb-2">
                  1. Cuisines ({selectedCuisines.length} selected)
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {DEFAULT_CUISINE_CHOICES.map((cu) => {
                    const active = selectedCuisines.includes(cu);
                    return (
                      <button
                        key={cu}
                        type="button"
                        onClick={() => toggleCuisine(cu)}
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs transition ${
                          active
                            ? "bg-tint-brand border-brand-600 text-ink font-semibold"
                            : "bg-well border-line text-ink-muted"
                        }`}
                      >
                        <CheckCircle2 className={`w-3.5 h-3.5 ${active ? "text-accent-brand" : "text-ink-subtle"}`} />
                        <span>{cu}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <p className="text-[11px] font-bold uppercase tracking-wider text-ink-muted mb-2">
                  2. Dish Categories ({categories.length} selected)
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {categories.map((c) => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => toggleCategory(c)}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-control border border-line-strong text-xs text-ink-2 hover:bg-well"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-accent-brand" />
                      <span>{c}</span>
                    </button>
                  ))}
                </div>
              </div>

              <label className="inline-flex items-center gap-2 text-xs text-ink-2 cursor-pointer pt-1">
                <input
                  type="checkbox"
                  checked={includeSampleDishes}
                  onChange={(e) => setIncludeSampleDishes(e.target.checked)}
                  className="w-4 h-4 rounded accent-brand-600"
                />
                <span>Include starter Indian dishes (Dosa, Biryani, Starters, Curries & Meals) + Breakfast/Lunch/Dinner schedules</span>
              </label>

              <div className="flex gap-2 pt-2">
                <input
                  type="text"
                  placeholder="Add custom dish category..."
                  value={newCat}
                  onChange={(e) => setNewCat(e.target.value)}
                  className="flex-1 px-3 py-2 bg-well border border-input-border rounded-lg text-sm text-ink"
                />
                <button
                  type="button"
                  onClick={() => {
                    const trimmed = newCat.trim();
                    if (trimmed && !categories.includes(trimmed)) {
                      setCategories([...categories, trimmed]);
                      setNewCat("");
                    }
                  }}
                  className="px-4 py-2 bg-control hover:bg-control-hover text-ink-2 text-xs font-semibold rounded-lg border border-line"
                >
                  Add
                </button>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-ink">Dining Areas & Tables</h2>
              <p className="text-xs text-ink-muted">Configure your initial dining hall and number of tables for POS visual layout.</p>
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">Primary Dining Area Name</label>
                <input
                  type="text"
                  value={diningArea}
                  onChange={(e) => setDiningArea(e.target.value)}
                  className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-sm text-ink"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-3 mb-1">Initial Tables Count</label>
                <input
                  type="number"
                  min={2}
                  max={50}
                  value={tableCount}
                  onChange={(e) => setTableCount(parseInt(e.target.value) || 8)}
                  className="w-full px-3 py-2 bg-well border border-input-border rounded-lg text-sm text-ink"
                />
              </div>
            </div>
          )}

          {step === 5 && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-ink">Kitchen Display Stations</h2>
              <p className="text-xs text-ink-muted">KOTs will automatically route items to their designated kitchen station.</p>
              <div className="space-y-2">
                {stations.map((st, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-well border border-line text-xs font-medium text-ink-2">
                    <MonitorCheck className="w-4 h-4 text-accent-sky" />
                    <span>{st}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Navigation Controls */}
          <div className="flex items-center justify-between mt-8 pt-6 border-t border-line">
            {step > 1 ? (
              <button
                type="button"
                onClick={() => setStep(step - 1)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-ink-muted hover:text-ink transition"
              >
                <ArrowLeft className="w-4 h-4" /> Previous
              </button>
            ) : <div />}

            {step < 5 ? (
              <button
                type="button"
                onClick={() => setStep(step + 1)}
                className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 shadow-md shadow-brand-500/20 transition"
              >
                Next Step <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleComplete}
                disabled={loading}
                className="flex items-center gap-2 px-6 py-2.5 rounded-lg text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 shadow-lg shadow-emerald-500/20 transition disabled:opacity-50"
              >
                {loading ? "Finishing Configuration..." : "Launch Restaurant Workspace"} <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
