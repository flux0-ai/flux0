import { useScrollToBottom } from "@/hooks/use-scroll-to-bottom";
import type { Message } from "@flux0-ai/react";
import equal from "fast-deep-equal";
import { memo } from "react";
import { PreviewMessage, ThinkingMessage } from "./message";

interface MessagesProps {
  sessionId: string;
  isLoading: boolean;
  messages: Array<Message>;
  setMessages: (
    messages: Message[] | ((messages: Message[]) => Message[]),
  ) => void;
  isReadonly: boolean;
  isBlockVisible: boolean;
}

function PureMessages({
  isLoading,
  messages,
  setMessages,
  isReadonly,
}: MessagesProps) {
  const [messagesContainerRef, messagesEndRef] =
    useScrollToBottom<HTMLDivElement>();

  return (
    <div
      ref={messagesContainerRef}
      className="flex flex-col min-w-0 gap-6 flex-1 overflow-y-scroll pt-4"
    >
      {messages.map((message, index) => (
        <PreviewMessage
          key={message.id}
          message={message}
          isLoading={isLoading && messages.length - 1 === index}
          setMessages={setMessages}
          isReadonly={isReadonly}
        />
      ))}

      {isLoading &&
        messages.length > 0 &&
        messages[messages.length - 1].source === "user" && <ThinkingMessage />}

      <div
        ref={messagesEndRef}
        className="shrink-0 min-w-[24px] min-h-[24px]"
      />
    </div>
  );
}

export const Messages = memo(PureMessages, (prevProps, nextProps) => {
  if (prevProps.isBlockVisible && nextProps.isBlockVisible) return true;
  if (prevProps.isLoading !== nextProps.isLoading) return false;
  if (prevProps.isLoading && nextProps.isLoading) return false;
  if (prevProps.messages.length !== nextProps.messages.length) return false;
  // TODO: seems like this is always true because react batches the updates
  // although text is actually streamed in the UI for some reason the messages contains in one render the whole content (all chunks)
  if (!equal(prevProps.messages, nextProps.messages)) return false;

  // TODO I changed this to false because of the equality issue above
  return false;
});
