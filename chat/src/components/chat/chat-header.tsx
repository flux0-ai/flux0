"use client";

import { GitHubIcon, PlusIcon } from "@/components/icons";
import { SidebarToggle } from "@/components/sidebar-toggle";
import { Button } from "@/components/ui/button";
import { useSidebar } from "@/components/ui/sidebar";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useNavigate } from "@tanstack/react-router";
import { memo } from "react";
import { useWindowSize } from "usehooks-ts";

function PureChatHeader() {
  const { open } = useSidebar();

  const { width: windowWidth } = useWindowSize();
  const navigate = useNavigate();

  return (
    <header className="flex sticky top-0 bg-background py-1.5 items-center px-2 md:px-2 gap-2">
      {(!open || windowWidth < 768) && <SidebarToggle />}

      {(!open || windowWidth < 768) && (
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              className="order-2 md:order-1 md:px-2 px-2 md:h-fit ml-auto md:ml-0"
              onClick={() => {
                navigate({ to: "/" });
              }}
            >
              <PlusIcon />
              <span className="md:sr-only">New Session</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent>New Chat</TooltipContent>
        </Tooltip>
      )}

      <Button
        className="bg-zinc-900 dark:bg-zinc-100 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-zinc-50 dark:text-zinc-900 hidden md:flex py-1.5 px-2 h-fit md:h-[34px] order-4 md:ml-auto"
        asChild
      >
        <a href="https://github.com/flux0-ai/flux0" target="_noblank">
          <GitHubIcon />
          Flux0
        </a>
      </Button>
    </header>
  );
}

export const ChatHeader = memo(PureChatHeader, () => {
  // e.g., if we don't want to re-render the component when the selectedModelId changes
  // return prevProps.selectedModelId === nextProps.selectedModelId;
  return true;
});
