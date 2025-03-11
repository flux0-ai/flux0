"use client";

import { PencilEditIcon, SparklesIcon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { Message } from "@flux0-ai/react";
import { cx } from "class-variance-authority";
import equal from "fast-deep-equal";
import { AnimatePresence, motion } from "motion/react";
import { memo, useState } from "react";
import { toast } from "sonner";
import { Markdown } from "../markdown";
import { MessageActions } from "./message-actions";
import { MessageEditor } from "./message-editor";
import { MessageReasoning } from "./message-reasoning";

const render_message_content = (message: Message) => {
  if (message.source) {
    if (
      Array.isArray(message.content) &&
      message.content.every((item) => typeof item === "string")
    ) {
      return <Markdown>{message.content.join("")}</Markdown>;
    }
    if (typeof message.content === "string") {
      return <Markdown>{message.content}</Markdown>;
    }
    return (
      <Markdown>{`\`\`\`json\n${JSON.stringify(message.content, null, 2)}\n\`\`\``}</Markdown>
    );
  }
};

const PurePreviewMessage = ({
  message,
  isLoading,
  setMessages,
  isReadonly,
}: {
  message: Message;
  isLoading: boolean;
  setMessages: (
    messages: Message[] | ((messages: Message[]) => Message[]),
  ) => void;
  isReadonly: boolean;
}) => {
  const [mode, setMode] = useState<"view" | "edit">("view");

  const reload = (): Promise<string | null | undefined> => {
    toast("Not supported yet!");
    return Promise.resolve(undefined);
  };

  // console.log(message.tool_calls)
  return (
    <AnimatePresence>
      <motion.div
        className="w-full mx-auto max-w-3xl px-4 group/message"
        initial={{ y: 5, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        data-role={message.source}
      >
        <div
          className={cn(
            "flex gap-4 w-full group-data-[role=user]/message:ml-auto group-data-[role=user]/message:max-w-2xl",
            {
              "w-full": mode === "edit",
              "group-data-[role=user]/message:w-fit": mode !== "edit",
            },
          )}
        >
          {message.source === "ai_agent" && (
            <div className="size-8 flex items-center rounded-full justify-center ring-1 shrink-0 ring-border bg-background">
              <div className="translate-y-px">
                <SparklesIcon size={14} />
              </div>
            </div>
          )}

          <div className="flex flex-col gap-4 w-full">
            {/* we may support attachments here such: if message.attachments -> map each attachment to PreviewAttachment*/}

            {message.reasoning && (
              <MessageReasoning
                isLoading={isLoading}
                reasoning={message.reasoning}
              />
            )}

            {message.content && !message.reasoning && mode === "view" && (
              <div className="flex flex-row gap-2 items-start">
                {message.source === "user" && !isReadonly && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        className="px-2 h-fit rounded-full text-muted-foreground opacity-0 group-hover/message:opacity-100"
                        onClick={() => {
                          setMode("edit");
                        }}
                      >
                        <PencilEditIcon />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Edit message</TooltipContent>
                  </Tooltip>
                )}

                <div
                  className={cn("flex flex-col gap-4", {
                    "bg-primary text-primary-foreground px-3 py-2 rounded-xl":
                      message.source === "user",
                  })}
                >
                  {render_message_content(message)}
                </div>
              </div>
            )}

            {message.content && mode === "edit" && (
              <div className="flex flex-row gap-2 items-start">
                <div className="size-8" />
                <MessageEditor
                  key={message.id}
                  message={message}
                  setMode={setMode}
                  setMessages={setMessages}
                  reload={reload}
                />
              </div>
            )}

            {message.tool_calls && message.tool_calls.length > 0 && (
              <div className="flex flex-col gap-4">
                {message.tool_calls.map((toolInvocation) => {
                  const { tool_name, tool_call_id, result } = toolInvocation;
                  if (result) {
                    return (
                      <div key={tool_call_id}>
                        {tool_name === "get_weather" ? (
                          <div>Custom Weather Component</div>
                        ) : (
                          <span className="text-muted-foreground/50">
                            {tool_name} : {JSON.stringify(result)}
                          </span>
                        )}
                      </div>
                    );
                  }

                  return (
                    <div
                      key={tool_call_id}
                      className={cx({
                        skeleton: ["get_weather"].includes(tool_name),
                      })}
                    >
                      <span className="text-muted-foreground/50">
                        {tool_name}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}

            {!isReadonly && (
              <MessageActions
                key={`action-${message.id}`}
                message={message}
                isLoading={isLoading}
              />
            )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export const PreviewMessage = memo(
  PurePreviewMessage,
  (prevProps, nextProps) => {
    if (prevProps.isLoading !== nextProps.isLoading) return false;
    if (prevProps.message.reasoning !== nextProps.message.reasoning)
      return false;
    if (prevProps.message.content !== nextProps.message.content) return false;
    if (!equal(prevProps.message.tool_calls, nextProps.message.tool_calls))
      return false;

    return false;
  },
);

export const ThinkingMessage = () => {
  const role = "ai_agent";

  return (
    <motion.div
      className="w-full mx-auto max-w-3xl px-4 group/message "
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1, transition: { delay: 1 } }}
      data-role={role}
    >
      <div
        className={cx(
          "flex gap-4 group-data-[role=user]/message:px-3 w-full group-data-[role=user]/message:w-fit group-data-[role=user]/message:ml-auto group-data-[role=user]/message:max-w-2xl group-data-[role=user]/message:py-2 rounded-xl",
          {
            "group-data-[role=user]/message:bg-muted": true,
          },
        )}
      >
        <div className="size-8 flex items-center rounded-full justify-center ring-1 shrink-0 ring-border">
          <SparklesIcon size={14} />
        </div>

        <div className="flex flex-col gap-2 w-full">
          <div className="flex flex-col gap-4 text-muted-foreground">
            Thinking...
          </div>
        </div>
      </div>
    </motion.div>
  );
};
