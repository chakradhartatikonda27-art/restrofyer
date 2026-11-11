"use client";

import { Pencil, Trash2 } from "lucide-react";
import { MenuItemRecord } from "./MenuTypes";
import { DietaryBadge, DishThumbnail } from "./VegBadge";

interface DishPhotoGridProps {
  items: MenuItemRecord[];
  onToggleAvailability: (itemId: string) => void;
  onToggleCustomerSite: (itemId: string) => void;
  onEdit: (item: MenuItemRecord) => void;
  onDelete: (item: MenuItemRecord) => void;
  emptyMessage?: string;
}

export function DishPhotoGrid({
  items,
  onToggleAvailability,
  onToggleCustomerSite,
  onEdit,
  onDelete,
  emptyMessage = "No dishes match the active filters.",
}: DishPhotoGridProps) {
  if (items.length === 0) {
    return (
      <div className="bg-panel border border-line rounded-2xl py-14 px-6 text-center text-xs text-ink-subtle shadow-sm">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {items.map((item) => {
        const displayPrice =
          typeof item.effective_price === "number" ? item.effective_price : item.base_price;
        const hasBranchOverride =
          typeof item.effective_price === "number" &&
          Math.abs(item.effective_price - item.base_price) > 0.001;

        return (
          <div
            key={item.id}
            className="bg-panel border border-line rounded-2xl overflow-hidden shadow-sm hover:border-line-strong transition flex flex-col justify-between group"
          >
            <div>
              {/* Dish Hero Photo */}
              <div className="relative h-40 w-full bg-well overflow-hidden">
                <DishThumbnail
                  imageUrl={item.image_url}
                  name={item.name}
                  className="w-full h-full rounded-none border-0 group-hover:scale-[1.02] transition-transform duration-300"
                />
                <div className="absolute top-2.5 left-2.5">
                  <DietaryBadge foodType={item.food_type} isVeg={item.is_veg} showLabel />
                </div>
                <div className="absolute top-2.5 right-2.5 flex items-center gap-1">
                  {item.is_combo && (
                    <span className="px-2 py-0.5 rounded-full bg-brand-600 text-white text-[10px] font-bold shadow">
                      Combo
                    </span>
                  )}
                  {!item.is_available && (
                    <span className="px-2 py-0.5 rounded-full bg-rose-600 text-white text-[10px] font-bold shadow">
                      Out of Stock
                    </span>
                  )}
                </div>
              </div>

              {/* Dish Meta & Title */}
              <div className="p-3.5 space-y-1.5">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-bold text-sm text-ink leading-snug line-clamp-1">
                    {item.name}
                  </h3>
                  <div className="text-right shrink-0">
                    <span className="font-extrabold text-sm text-ink font-mono">
                      ₹{displayPrice.toFixed(0)}
                    </span>
                    {hasBranchOverride && (
                      <div className="text-[10px] text-ink-subtle line-through font-mono">
                        ₹{item.base_price.toFixed(0)}
                      </div>
                    )}
                  </div>
                </div>

                <p className="text-[11px] font-medium text-accent-brand line-clamp-1">
                  {item.cuisine_name || "Indian"} · {item.category_name || "Dish"}
                </p>

                {item.description && (
                  <p className="text-[11px] text-ink-muted line-clamp-2 leading-relaxed">
                    {item.description}
                  </p>
                )}
              </div>
            </div>

            {/* Clean Footer Switches & Actions */}
            <div className="px-3.5 py-2.5 bg-well/60 border-t border-line flex items-center justify-between gap-2 text-[11px]">
              <div className="flex items-center gap-3 text-ink-2">
                <label className="inline-flex items-center gap-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={item.is_available}
                    onChange={() => onToggleAvailability(item.id)}
                    className="w-3.5 h-3.5 rounded accent-brand-600"
                  />
                  <span>Stock</span>
                </label>
                <label className="inline-flex items-center gap-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={item.show_on_customer_site}
                    onChange={() => onToggleCustomerSite(item.id)}
                    className="w-3.5 h-3.5 rounded accent-brand-600"
                  />
                  <span>Online</span>
                </label>
              </div>

              <div className="inline-flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => onEdit(item)}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-line-strong bg-panel hover:bg-control text-ink-2 text-[11px] font-semibold transition"
                >
                  <Pencil className="w-3 h-3" />
                  <span>Edit</span>
                </button>
                <button
                  type="button"
                  onClick={() => onDelete(item)}
                  title={`Delete ${item.name}`}
                  aria-label={`Delete ${item.name}`}
                  className="p-1.5 rounded-lg border border-tint-rose-border bg-tint-rose text-accent-rose hover:opacity-80 transition"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
