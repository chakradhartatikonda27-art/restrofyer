"use client";

import { Pencil, Trash2 } from "lucide-react";
import { MenuItemRecord } from "./MenuTypes";
import { DietaryBadge, DishThumbnail } from "./VegBadge";

interface MenuItemTableProps {
  items: MenuItemRecord[];
  onToggleAvailability: (itemId: string) => void;
  onToggleCustomerSite: (itemId: string) => void;
  onEdit: (item: MenuItemRecord) => void;
  onDelete: (item: MenuItemRecord) => void;
  emptyMessage?: string;
}

export function MenuItemTable({
  items,
  onToggleAvailability,
  onToggleCustomerSite,
  onEdit,
  onDelete,
  emptyMessage = "No menu items match the selected filter.",
}: MenuItemTableProps) {
  return (
    <div className="bg-panel border border-line rounded-2xl overflow-hidden shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-well text-ink-muted border-b border-line uppercase tracking-wider text-[10px]">
            <tr>
              <th className="py-3 px-4 font-bold">Dish</th>
              <th className="py-3 px-3 font-bold">Food Type</th>
              <th className="py-3 px-3 font-bold">Category & Cuisine</th>
              <th className="py-3 px-3 font-bold">Price</th>
              <th className="py-3 px-3 font-bold">Status</th>
              <th className="py-3 px-4 font-bold text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {items.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-xs text-ink-subtle">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              items.map((item) => {
                const displayPrice =
                  typeof item.effective_price === "number" ? item.effective_price : item.base_price;
                const hasBranchOverride =
                  typeof item.effective_price === "number" &&
                  Math.abs(item.effective_price - item.base_price) > 0.001;

                return (
                  <tr key={item.id} className="hover:bg-row-hover transition">
                    <td className="py-3 px-4">
                      <div className="flex items-start gap-3">
                        <DishThumbnail imageUrl={item.image_url} name={item.name} />
                        <div className="min-w-0 max-w-md">
                          <div className="flex flex-wrap items-center gap-1.5">
                            <DietaryBadge foodType={item.food_type} isVeg={item.is_veg} />
                            <span className="font-bold text-sm text-ink truncate">{item.name}</span>
                            {item.is_combo && (
                              <span className="px-1.5 py-0.5 rounded bg-tint-brand text-accent-brand border border-tint-brand-border text-[10px] font-bold">
                                Combo
                              </span>
                            )}
                            {item.variants && item.variants.length > 0 && (
                              <span className="px-1.5 py-0.5 rounded bg-well text-ink-muted border border-line text-[10px]">
                                {item.variants.length} sizes
                              </span>
                            )}
                          </div>
                          {item.description && (
                            <p className="text-[11px] text-ink-muted line-clamp-1 mt-0.5">
                              {item.description}
                            </p>
                          )}
                          <p className="text-[10px] text-ink-subtle mt-0.5">
                            {item.kitchen_station_name ? `KOT: ${item.kitchen_station_name} · ` : ""}
                            GST {item.tax_rate}%
                          </p>
                        </div>
                      </div>
                    </td>

                    <td className="py-3 px-3 whitespace-nowrap">
                      <DietaryBadge foodType={item.food_type} isVeg={item.is_veg} showLabel />
                    </td>

                    <td className="py-3 px-3 whitespace-nowrap">
                      <div className="font-semibold text-ink">
                        {item.category_name || "Uncategorized"}
                      </div>
                      <div className="text-[11px] text-ink-muted mt-0.5">
                        {item.cuisine_name || "All Cuisines"}
                        {item.menu_name ? ` · ${item.menu_name}` : ""}
                      </div>
                    </td>

                    <td className="py-3 px-3 whitespace-nowrap">
                      <div className="font-bold text-ink">₹{displayPrice.toFixed(2)}</div>
                      {hasBranchOverride && (
                        <div className="text-[10px] text-ink-subtle line-through">
                          ₹{item.base_price.toFixed(2)} base
                        </div>
                      )}
                    </td>

                    <td className="py-3 px-3 whitespace-nowrap">
                      <div className="flex flex-col gap-1.5 text-[11px] text-ink-2">
                        <label className="inline-flex items-center gap-1.5 cursor-pointer">
                          <input
                            type="checkbox"
                            aria-label={`Toggle availability for ${item.name}`}
                            checked={item.is_available}
                            onChange={() => onToggleAvailability(item.id)}
                            className="w-3.5 h-3.5 rounded accent-brand-600 cursor-pointer"
                          />
                          <span>In Stock</span>
                        </label>
                        <label className="inline-flex items-center gap-1.5 cursor-pointer">
                          <input
                            type="checkbox"
                            aria-label={`Toggle customer site visibility for ${item.name}`}
                            checked={item.show_on_customer_site}
                            onChange={() => onToggleCustomerSite(item.id)}
                            className="w-3.5 h-3.5 rounded accent-brand-600 cursor-pointer"
                          />
                          <span>Online</span>
                        </label>
                      </div>
                    </td>

                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => onEdit(item)}
                          className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-line-strong bg-panel hover:bg-control text-ink-2 text-xs font-semibold transition"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                          <span>Edit</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => onDelete(item)}
                          title={`Delete ${item.name}`}
                          aria-label={`Delete ${item.name}`}
                          className="p-1.5 rounded-lg border border-tint-rose-border bg-tint-rose text-accent-rose hover:opacity-80 transition"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
