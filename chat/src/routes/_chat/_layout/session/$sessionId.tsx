import { Chat } from "@/components/chat/chat";
import { fetchClientWithThrow } from "@/lib/api/api";
import type { ErrorComponentProps } from "@tanstack/react-router";
import { ErrorComponent, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_chat/_layout/session/$sessionId")({
  // load the session along with its events
  // note: we could defer the loading of the events as it takes more time (we'll show a 'loading...' meanwhile) by returning the promise
  // but putting content under Await causes page to render once navigation changes which removes the focus from the chat input
  loader: async ({ params: { sessionId } }) => {
    const session = await fetchClientWithThrow.GET(
      "/api/sessions/{session_id}",
      {
        params: { path: { session_id: sessionId } },
      },
    );

    const events = await fetchClientWithThrow.GET(
      "/api/sessions/{session_id}/events",
      {
        params: {
          path: { session_id: sessionId },
        },
      },
    );

    return {
      session,
      events,
    };
  },
  errorComponent: SessionErrorComponent,
  component: SessionComponent,
});

function SessionErrorComponent({ error }: ErrorComponentProps) {
  return <ErrorComponent error={error} />;
}

function SessionComponent() {
  const { session, events } = Route.useLoaderData();
  const { sessionId } = Route.useParams();
  if (!session || !session.data) return null;

  return (
    <Chat
      agentId={session.data.agent_id}
      sessionId={sessionId}
      initialEvents={events.data?.data || []}
      isReadonly={false}
    />
  );
}
