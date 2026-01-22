import * as React from "react";
import { cn } from "@/lib/utils";

export interface SwitchProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  label?: string;
}

const Switch = React.forwardRef<HTMLInputElement, SwitchProps>(
  ({ className, checked, onCheckedChange, label, ...props }, ref) => {
    return (
      <label className={cn("inline-flex items-center gap-2", className)}>
        {label && <span className="text-sm text-muted-foreground">{label}</span>}
        <span className="relative inline-flex h-6 w-10 items-center rounded-full bg-muted transition-colors">
          <input
            type="checkbox"
            ref={ref}
            className="peer sr-only"
            checked={checked}
            onChange={(e) => onCheckedChange?.(e.target.checked)}
            {...props}
          />
          <span className="absolute left-1 inline-block h-4 w-4 rounded-full bg-background shadow transition-transform peer-checked:translate-x-4" />
          <span className="absolute inset-0 rounded-full peer-checked:bg-primary/80" />
        </span>
      </label>
    );
  }
);
Switch.displayName = "Switch";

export { Switch };
