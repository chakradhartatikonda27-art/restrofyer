"use client";

import { useEffect, useState } from "react";
import { Utensils } from "lucide-react";
import type { FoodType } from "./MenuTypes";

export const DISH_PHOTO_PRESETS: { label: string; url: string }[] = [
  { label: "Masala Dosa", url: "/images/dishes/masala-dosa.jpg" },
  { label: "Idli & Vada", url: "/images/dishes/idli-vada.jpg" },
  { label: "Chicken 65", url: "/images/dishes/chicken-65.jpg" },
  { label: "Paneer Tikka", url: "/images/dishes/paneer-tikka.jpg" },
  { label: "Curries & Gravy", url: "/images/dishes/paneer-butter-masala.jpg" },
  { label: "Dum Biryani", url: "/images/dishes/chicken-biryani.jpg" },
  { label: "Thali Meals", url: "/images/dishes/south-indian-meals.jpg" },
  { label: "Egg Curry", url: "/images/dishes/egg-curry.jpg" },
  { label: "Samosa & Chaat", url: "/images/dishes/samosa-snacks.jpg" },
  { label: "Dessert & Coffee", url: "/images/dishes/gulab-jamun-coffee.jpg" },
];

export function resolveFoodType(foodType?: FoodType | string | null, isVeg?: boolean): FoodType {
  if (foodType === "VEG" || foodType === "NON_VEG" || foodType === "EGG" || foodType === "VEGAN") {
    return foodType;
  }
  return isVeg === false ? "NON_VEG" : "VEG";
}

const FOOD_TYPE_META: Record<
  FoodType,
  {
    label: string;
    shortLabel: string;
    border: string;
    dot: string;
    pillClass: string;
  }
> = {
  VEG: {
    label: "Vegetarian",
    shortLabel: "Veg",
    border: "border-emerald-600",
    dot: "bg-emerald-600",
    pillClass: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/30",
  },
  NON_VEG: {
    label: "Non-Vegetarian",
    shortLabel: "Non-Veg",
    border: "border-rose-600",
    dot: "bg-rose-600",
    pillClass: "bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-500/30",
  },
  EGG: {
    label: "Egg",
    shortLabel: "Egg",
    border: "border-amber-600",
    dot: "bg-amber-500",
    pillClass: "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30",
  },
  VEGAN: {
    label: "Vegan",
    shortLabel: "Vegan",
    border: "border-teal-600",
    dot: "bg-teal-600",
    pillClass: "bg-teal-500/10 text-teal-700 dark:text-teal-300 border-teal-500/30",
  },
};

/**
 * Indian FSSAI dietary marker square (Veg, Non-Veg, Egg, Vegan) with optional semantic label pill.
 */
export function DietaryBadge({
  isVeg,
  foodType,
  showLabel = false,
}: {
  isVeg?: boolean;
  foodType?: FoodType | string | null;
  showLabel?: boolean;
}) {
  const resolved = resolveFoodType(foodType, isVeg);
  const meta = FOOD_TYPE_META[resolved];

  if (showLabel) {
    return (
      <span
        title={meta.label}
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-semibold border whitespace-nowrap ${meta.pillClass}`}
      >
        <span className={`inline-flex items-center justify-center w-3 h-3 rounded-[2px] border shrink-0 bg-panel ${meta.border}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
        </span>
        {meta.shortLabel}
      </span>
    );
  }

  return (
    <span
      title={meta.label}
      className={`inline-flex items-center justify-center w-3.5 h-3.5 rounded-[3px] border shrink-0 bg-panel ${meta.border}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
    </span>
  );
}

/**
 * Resilient dish photo container with graceful fallback to kitchen utensil icon.
 */
export function DishThumbnail({
  imageUrl,
  name,
  className = "w-14 h-14 rounded-xl",
}: {
  imageUrl?: string | null;
  name: string;
  className?: string;
}) {
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setFailed(false);
  }, [imageUrl]);

  if (imageUrl && !failed) {
    return (
      <img
        src={imageUrl}
        alt={name}
        onError={() => setFailed(true)}
        className={`${className} object-cover border border-line shrink-0 bg-well`}
      />
    );
  }
  return (
    <div
      className={`${className} border border-line bg-well flex items-center justify-center text-ink-muted shrink-0`}
    >
      <Utensils className="w-5 h-5 stroke-[1.5]" />
    </div>
  );
}
