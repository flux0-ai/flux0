"use client";

import { AlertTriangleIcon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { AnimatePresence, motion } from "motion/react";
import { memo } from "react";

interface ErrorMessageProps {
  error: string;
  onRetry?: () => void;
  className?: string;
}

const PureErrorMessage = ({ error, onRetry, className }: ErrorMessageProps) => {
  return (
    <AnimatePresence>
      <motion.div
        className={cn("w-full mx-auto max-w-3xl px-4 group/message", className)}
        initial={{ y: 5, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        data-role="error"
      >
        <div className="flex gap-4 w-full">
          <div className="size-8 flex items-center rounded-full justify-center ring-1 shrink-0 ring-destructive bg-destructive/10">
            <div className="translate-y-px text-destructive">
              <AlertTriangleIcon size={14} />
            </div>
          </div>

          <div className="flex flex-col gap-4 w-full">
            <div className="flex flex-col gap-2">
              <div className="text-sm font-medium text-destructive">
                Error occurred
              </div>
              <div className="text-sm text-muted-foreground bg-destructive/5 border border-destructive/20 rounded-lg p-3">
                {error}
              </div>
            </div>

            {onRetry && (
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onRetry}
                  className="text-xs"
                >
                  Try again
                </Button>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export const ErrorMessage = memo(PureErrorMessage);
