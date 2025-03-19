import { toast } from "sonner";
import { useCopyToClipboard } from "usehooks-ts";

import { CopyIcon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { Message } from "@flux0-ai/react";
import { memo } from "react";

export function PureMessageActions({
  message,
  processing,
}: {
  message: Message;
  processing: string | undefined;
}) {
  const [, copyToClipboard] = useCopyToClipboard();

  if (processing) return null;
  if (message.source === "user") return null;
  if (message.tool_calls && message.tool_calls.length > 0) return null;

  return (
    <TooltipProvider delayDuration={0}>
      <div className="flex flex-row gap-2">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              className="py-1 px-2 h-fit text-muted-foreground"
              variant="outline"
              onClick={async () => {
                await copyToClipboard(message.content as string);
                toast.success("Copied to clipboard!");
              }}
            >
              <CopyIcon />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Copy</TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
}

export const MessageActions = memo(
  PureMessageActions,
  (prevProps, nextProps) => {
    if (prevProps.processing !== nextProps.processing) return false;

    return true;
  },
);
