"use client";

import { useEffect, useId, useRef } from "react";
import { X } from "lucide-react";

interface ModalDialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  maxWidthClass?: string;
  children: React.ReactNode;
}

/**
 * Accessible native modal dialog using <dialog> + showModal() with closedby="any"
 * and pointer-bounds fallback for browsers without native closedBy support.
 */
export function ModalDialog({
  open,
  onClose,
  title,
  subtitle,
  maxWidthClass = "max-w-lg",
  children,
}: ModalDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const handleNativeClose = () => {
      if (open) onClose();
    };
    dialog.addEventListener("close", handleNativeClose);

    // Fallback light-dismiss when native closedby="any" is unsupported (e.g. Safari)
    let cleanupOutside: (() => void) | undefined;
    if (!("closedBy" in HTMLDialogElement.prototype)) {
      let pressedOutside = false;
      const isOutside = (e: PointerEvent) => {
        const r = dialog.getBoundingClientRect();
        return (
          e.clientX < r.left ||
          e.clientX > r.right ||
          e.clientY < r.top ||
          e.clientY > r.bottom
        );
      };
      const onPointerDown = (e: PointerEvent) => {
        pressedOutside = isOutside(e);
      };
      const onPointerUp = (e: PointerEvent) => {
        if (pressedOutside && isOutside(e)) {
          dialog.close();
        }
      };
      dialog.addEventListener("pointerdown", onPointerDown);
      dialog.addEventListener("pointerup", onPointerUp);
      cleanupOutside = () => {
        dialog.removeEventListener("pointerdown", onPointerDown);
        dialog.removeEventListener("pointerup", onPointerUp);
      };
    }

    return () => {
      dialog.removeEventListener("close", handleNativeClose);
      cleanupOutside?.();
    };
  }, [open, onClose]);

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={titleId}
      {...({ closedby: "any" } as Record<string, string>)}
      className={`w-[calc(100%-2rem)] ${maxWidthClass} m-auto rounded-2xl border border-line bg-panel text-ink-2 p-0 shadow-2xl`}
    >
      {open ? (
        <div className="p-6 space-y-4">
          <div className="flex items-start justify-between gap-4 border-b border-line pb-3">
            <div>
              <h3 id={titleId} className="text-base font-bold text-ink">
                {title}
              </h3>
              {subtitle && <p className="text-xs text-ink-muted mt-0.5">{subtitle}</p>}
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close dialog"
              className="p-1 rounded-lg text-ink-muted hover:text-ink hover:bg-control transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          {children}
        </div>
      ) : null}
    </dialog>
  );
}
