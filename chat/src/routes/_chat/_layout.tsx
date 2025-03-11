import { AppSidebar } from "@/components/app-sidebar";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import useCookie from "@/hooks/use-cookie";
import { StreamProvider } from "@flux0-ai/react";
import { Outlet, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_chat/_layout")({
  component: LayoutComponent,
});

function LayoutComponent() {
  const [sidebarStateValue] = useCookie("sidebar_state");
  const isCollapsed = sidebarStateValue !== "true";

  return (
    <SidebarProvider defaultOpen={!isCollapsed}>
      <AppSidebar
        user={{ id: "1234", name: "anonymous", email: "anonymous@acme.io" }}
      />
      <SidebarInset>
        <StreamProvider>
          <Outlet />
        </StreamProvider>
      </SidebarInset>
    </SidebarProvider>
  );
}
