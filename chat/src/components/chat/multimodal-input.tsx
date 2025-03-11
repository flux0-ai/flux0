"use client";

import { ArrowUpIcon, StopIcon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { fetchClientWithThrow } from "@/lib/api/api";
import { useQueryClient } from "@tanstack/react-query";
import { memo, useCallback, useEffect, useRef } from "react";
import { toast } from "sonner";
import { useLocalStorage, useWindowSize } from "usehooks-ts";

// check vercel's ai ChatRequestOptions for some ideas
function PureMultimodalInput({
  agentId,
  sessionId,
  newSession,
  input,
  setInput,
  handleSubmit,
  hasMessages,
  isLoading,
}: {
  agentId: string;
  sessionId: string;
  newSession?: boolean;
  input: string;
  setInput: (value: string) => void;
  isLoading: boolean;
  stop: () => void;
  handleSubmit: (
    event?: {
      preventDefault?: () => void;
    },
    // chatRequestOptions?: ChatRequestOptions,
  ) => void;
  hasMessages: boolean;
}) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { width } = useWindowSize();
  const queyrClient = useQueryClient();

  useEffect(() => {
    if (sessionId && textareaRef.current) {
      textareaRef.current?.focus();
    }
  }, [sessionId]);

  useEffect(() => {
    if (textareaRef.current) {
      adjustHeight();
    }
  }, []);

  const adjustHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight + 2}px`;
    }
  };

  const resetHeight = useCallback(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = "98px";
    }
  }, []);

  const [localStorageInput, setLocalStorageInput] = useLocalStorage(
    "input",
    "",
  );

  // biome-ignore lint/correctness/useExhaustiveDependencies: Only run once after hydration
  useEffect(() => {
    if (textareaRef.current) {
      const domValue = textareaRef.current.value;
      // Prefer DOM value over localStorage to handle hydration
      const finalValue = domValue || localStorageInput || "";
      setInput(finalValue);
      adjustHeight();
    }
  }, []);

  useEffect(() => {
    setLocalStorageInput(input);
  }, [input, setLocalStorageInput]);

  const handleInput = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(event.target.value);
    adjustHeight();
  };

  const submitForm = useCallback(async () => {
    if (newSession) {
      await fetchClientWithThrow.POST("/api/sessions", {
        body: {
          id: sessionId,
          title: input.split(" ").reduce((acc, word) => {
            if (acc.length + word.length + 1 <= 15) {
              return acc + (acc ? " " : "") + word;
            }
            return acc;
          }, ""),
          agent_id: agentId,
        },
      });
      queyrClient.invalidateQueries({ queryKey: ["get", "/api/sessions", {}] });
    }

    // navigate({ to: '/session/$sessionId', params: { sessionId: sessionIdToRedir } });
    window.history.replaceState({}, "", `/chat/session/${sessionId}`);

    handleSubmit(undefined);
    setLocalStorageInput("");
    resetHeight();

    // do we need this?
    if (width && width > 768) {
      textareaRef.current?.focus();
    }
  }, [
    handleSubmit,
    setLocalStorageInput,
    width,
    sessionId,
    agentId,
    input,
    newSession,
    queyrClient,
    resetHeight,
  ]);

  return (
    <div className="relative w-full flex flex-col gap-4">
      {!isLoading && !hasMessages && (
        // <SuggestedActions append={append} sessionId={sessionId} />
        <div>No messages yet</div>
      )}

      <Textarea
        ref={textareaRef}
        placeholder="Send a message..."
        value={input}
        onChange={handleInput}
        className={
          "min-h-[24px] max-h-[calc(75dvh)] overflow-hidden resize-none rounded-2xl !text-base bg-muted pb-10 dark:border-zinc-700"
        }
        rows={2}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();

            if (isLoading) {
              toast("Please wait for the model to finish its response!");
            } else {
              submitForm();
            }
          }
        }}
      />

      <div className="absolute bottom-0 right-0 p-2 w-fit flex flex-row justify-end">
        {isLoading ? (
          <StopButton stop={stop} />
        ) : (
          <SendButton input={input} submitForm={submitForm} />
        )}
      </div>
    </div>
  );
}

export const MultimodalInput = memo(
  PureMultimodalInput,
  (prevProps, nextProps) => {
    if (prevProps.input !== nextProps.input) return false;
    if (prevProps.isLoading !== nextProps.isLoading) return false;
    if (prevProps.hasMessages !== nextProps.hasMessages) return false;
    if (prevProps.agentId !== nextProps.agentId) return false;
    if (prevProps.sessionId !== nextProps.sessionId) return false;

    return true;
  },
);

function PureStopButton({
  stop,
  // setMessages,
}: {
  stop: () => void;
  // setMessages: Dispatch<SetStateAction<Array<Message>>>;
}) {
  return (
    <Button
      className="rounded-full p-1.5 h-fit border dark:border-zinc-600"
      onClick={(event) => {
        event.preventDefault();
        stop();
        // setMessages((messages) => sanitizeUIMessages(messages));
      }}
    >
      <StopIcon size={14} />
    </Button>
  );
}

const StopButton = memo(PureStopButton);

function PureSendButton({
  submitForm,
  input,
}: { submitForm: () => void; input: string }) {
  return (
    <Button
      className="rounded-full p-1.5 h-fit border dark:border-zinc-600"
      onClick={(event) => {
        event.preventDefault();
        submitForm();
      }}
      disabled={input.length === 0}
    >
      <ArrowUpIcon size={14} />
    </Button>
  );
}

const SendButton = memo(PureSendButton, (prevProps, nextProps) => {
  if (prevProps.input !== nextProps.input) return false;
  return true;
});
