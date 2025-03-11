import { Chat } from "@/components/chat/chat";
import { fetchClientWithThrow } from "@/lib/api/api";
import type { ErrorComponentProps } from "@tanstack/react-router";
import { ErrorComponent, createFileRoute } from "@tanstack/react-router";
import { nanoid } from "nanoid";

export const Route = createFileRoute("/_chat/_layout/agent/$agentId")({
  // load the session along with its events
  // note: we could defer the loading of the events as it takes more time (we'll show a 'loading...' meanwhile) by returning the promise
  // but putting content under Await causes page to render once navigation changes which removes the focus from the chat input
  loader: async ({ params: { agentId } }) => {
    const agent = await fetchClientWithThrow.GET("/api/agents/{agent_id}", {
      params: { path: { agent_id: agentId } },
    });

    return {
      agent,
    };
  },
  errorComponent: SessionErrorComponent,
  component: SessionComponent,
});

function SessionErrorComponent({ error }: ErrorComponentProps) {
  return <ErrorComponent error={error} />;
}

function SessionComponent() {
  const { agent } = Route.useLoaderData();
  if (!agent || !agent.data) return null;

  return (
    <Chat
      agentId={agent.data.id}
      sessionId={nanoid(10)}
      newSession
      initialEvents={[]}
      isReadonly={false}
    />
  );
}
