import type { components } from "@/lib/api/v1";
import { useMessageStream } from "@flux0-ai/react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { ChatHeader } from "./chat-header";
import { Messages } from "./messages";
import { MultimodalInput } from "./multimodal-input";

export function Chat({
  agentId,
  sessionId,
  newSession,
  initialEvents,
  isReadonly,
}: {
  agentId: string;
  sessionId: string;
  newSession?: boolean;
  initialEvents: Array<components["schemas"]["EventDTO"]>;
  isReadonly: boolean;
}) {
  const [input, setInput] = useState<string>("");

  const {
    messages,
    streaming,
    isThinking,
    error,
    resetEvents,
    startStreaming,
    stopStreaming,
  } = useMessageStream({ events: initialEvents });

  const handleSubmit = useCallback(
    (event?: { preventDefault?: () => void }) => {
      if (event) {
        event.preventDefault?.();
      }
      startStreaming(sessionId, input);
      setInput("");
    },
    [startStreaming, input, sessionId],
  );

  useEffect(() => {
    return () => {
      resetEvents();
    };
  }, [resetEvents]);

  useEffect(() => {
    if (error) {
      toast(error.message);
    }
  }, [error]);

  return (
    <div className="flex flex-col min-w-0 h-dvh bg-background">
      <ChatHeader />
      <Messages
        sessionId={sessionId}
        isLoading={isThinking}
        messages={Array.from(messages.values())}
        setMessages={() => {
          // const messageMap = new Map(updatedMessages.map((msg) => [msg.id, msg]));
          // setMessages(messageMap);
        }}
        isReadonly={isReadonly}
        isBlockVisible={false}
      />
      <form className="flex mx-auto px-4 bg-background pb-4 md:pb-6 gap-2 w-full md:max-w-3xl">
        {!isReadonly && (
          <MultimodalInput
            agentId={agentId}
            newSession={newSession}
            sessionId={sessionId}
            input={input}
            setInput={setInput}
            handleSubmit={handleSubmit}
            isLoading={streaming}
            stop={stopStreaming}
            hasMessages={!!messages.length}
          />
        )}
      </form>
    </div>
  );
}
