import { ChatHeader } from "@/components/chat/chat-header";
import { fetchClientWithThrow } from "@/lib/api/api";
import { cn } from "@/lib/utils";
import { ErrorComponent, Link, createFileRoute } from "@tanstack/react-router";
import { BotIcon } from "lucide-react";

export const Route = createFileRoute("/_chat/_layout/")({
  loader: async () => {
    const agents = await fetchClientWithThrow.GET("/api/agents");

    return {
      agents,
    };
  },
  errorComponent: ErrorComponent,
  component: Index,
});

function Index() {
  const { agents: agentsResult } = Route.useLoaderData();
  const agents = agentsResult.data?.data || [];

  return (
    <div className="flex flex-col flex-1">
      <ChatHeader />
      <div className="flex flex-1 flex-col gap-4 p-4 justify-center">
        <div className="divide-y divide-border overflow-hidden rounded-lg shadow sm:grid sm:grid-cols-2 sm:gap-1 sm:divide-y-0">
          {agents.map((agent, agentIdx) => (
            <div
              key={agent.id}
              className={cn(
                agentIdx === 0
                  ? "rounded-tl-lg rounded-tr-lg sm:rounded-tr-none"
                  : "",
                agentIdx === 1 ? "sm:rounded-tr-lg" : "",
                agentIdx === agents.length - 2 ? "sm:rounded-bl-lg" : "",
                agentIdx === agents.length - 1
                  ? "rounded-bl-lg rounded-br-lg sm:rounded-bl-none"
                  : "",
                "group relative bg-muted/40 p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-ring",
              )}
            >
              <div>
                <span
                  className={cn(
                    "inline-flex rounded-lg p-3 ring-4 ring-secondary",
                  )}
                >
                  <BotIcon aria-hidden="true" className="size-6" />
                </span>
              </div>
              <div className="mt-8">
                <h3 className="text-base font-semibold">
                  <Link
                    to="/agent/$agentId"
                    params={{ agentId: agent.id }}
                    className="focus:outline-none"
                  >
                    {/* Extend touch target to entire panel */}
                    <span aria-hidden="true" className="absolute inset-0" />
                    {agent.name}
                  </Link>
                </h3>
                {/* may put here agent's description
                            <p className="mt-2 text-sm text-gray-500">
                            ...
                            </p>
                            */}
              </div>
              <span
                aria-hidden="true"
                className="pointer-events-none absolute right-6 top-6 text-muted-foreground/20 group-hover:text-muted-foreground/40"
              >
                <svg fill="currentColor" viewBox="0 0 24 24" className="size-6">
                  <title>Open</title>
                  <path d="M20 4h1a1 1 0 00-1-1v1zm-1 12a1 1 0 102 0h-2zM8 3a1 1 0 000 2V3zM3.293 19.293a1 1 0 101.414 1.414l-1.414-1.414zM19 4v12h2V4h-2zm1-1H8v2h12V3zm-.707.293l-16 16 1.414 1.414 16-16-1.414-1.414z" />
                </svg>
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
