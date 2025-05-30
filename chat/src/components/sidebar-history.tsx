"use client";
import { $api } from "@/lib/api/api";
import type { Session, User } from "@/lib/api/types";
import { Link, useParams } from "@tanstack/react-router";
import { isToday, isYesterday, subMonths, subWeeks } from "date-fns";
import { memo, useState } from "react";
import { MoreHorizontalIcon, TrashIcon } from "./icons";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "./ui/alert-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "./ui/sidebar";

type GroupedSessions = {
  today: Session[];
  yesterday: Session[];
  lastWeek: Session[];
  lastMonth: Session[];
  older: Session[];
};

interface PureSessionItemProps {
  session: Session;
  isActive: boolean;
  onDelete: (chatId: string) => void;
  setOpenMobile: (open: boolean) => void;
}

const PureSessionItem = ({
  session,
  isActive,
  onDelete,
  setOpenMobile,
}: PureSessionItemProps) => {
  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild isActive={isActive}>
        {/* className="[&.active]:font-bold"  */}
        <Link
          to={"/session/$sessionId"}
          params={{ sessionId: session.id }}
          onClick={() => setOpenMobile(false)}
        >
          <span>{session.title}</span>
        </Link>
      </SidebarMenuButton>

      <DropdownMenu modal={true}>
        <DropdownMenuTrigger asChild>
          <SidebarMenuAction
            className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground mr-0.5"
            showOnHover={!isActive}
          >
            <MoreHorizontalIcon />
            <span className="sr-only">More</span>
          </SidebarMenuAction>
        </DropdownMenuTrigger>

        <DropdownMenuContent side="bottom" align="end">
          <DropdownMenuItem
            className="cursor-pointer text-destructive focus:bg-destructive/15 focus:text-destructive dark:text-red-500"
            onSelect={() => onDelete(session.id)}
          >
            <TrashIcon />
            <span>Delete</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </SidebarMenuItem>
  );
};

export const SessionItem = memo(PureSessionItem, (prevProps, nextProps) => {
  if (prevProps.isActive !== nextProps.isActive) return false;
  return true;
});

export function SidebarHistory({ user }: { user: User | undefined }) {
  const { setOpenMobile } = useSidebar();
  // const queryClient = useQueryClient();
  // const navigate = useNavigate();

  const { sessionId } = useParams({ strict: false });

  const { data: history, isLoading } = $api.useQuery(
    "get",
    "/api/sessions",
    {},
    {
      select: (data) => data.data,
    },
  );

  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const handleDelete = async () => {
    if (!deleteId) return;
    // TODO!
    // const deletePromise = fetchClientWithThrow.DELETE(
    //   "/api/sessions/{session_id}",
    //   {
    //     params: {
    //       path: {
    //         session_id: deleteId,
    //       },
    //     },
    //   },
    // );

    // toast.promise(deletePromise, {
    //   loading: "Deleting session...",
    //   success: () => {
    //     queryClient.setQueryData(
    //       ["get", "/api/sessions", {}],
    //       (oldHistory: { data: Session[] }) => {
    //         if (oldHistory) {
    //           return { data: oldHistory.data.filter((h) => h.id !== deleteId) };
    //         }
    //         return oldHistory;
    //       },
    //     );
    //     return "Session deleted successfully";
    //   },
    //   error: "Failed to delete session",
    // });

    // if (deleteId === sessionId) {
    //   navigate({ to: "/" });
    // }
  };

  if (!user) {
    return (
      <SidebarGroup>
        <SidebarGroupContent>
          <div className="px-2 text-zinc-500 w-full flex flex-row justify-center items-center text-sm gap-2">
            Login to save and revisit previous chats!
          </div>
        </SidebarGroupContent>
      </SidebarGroup>
    );
  }

  if (isLoading) {
    return (
      <SidebarGroup>
        <div className="px-2 py-1 text-xs text-sidebar-foreground/50">
          Today
        </div>
        <SidebarGroupContent>
          <div className="flex flex-col">
            {[44, 32, 28, 64, 52].map((item) => (
              <div
                key={item}
                className="rounded-md h-8 flex gap-2 px-2 items-center"
              >
                <div
                  className="h-4 rounded-md flex-1 max-w-(length:--skeleton-width) bg-sidebar-accent-foreground/10"
                  style={
                    {
                      "--skeleton-width": `${item}%`,
                    } as React.CSSProperties
                  }
                />
              </div>
            ))}
          </div>
        </SidebarGroupContent>
      </SidebarGroup>
    );
  }

  if (history?.length === 0) {
    return (
      <SidebarGroup>
        <SidebarGroupContent>
          <div className="px-2 text-zinc-500 w-full flex flex-row justify-center items-center text-sm gap-2">
            Your conversations will appear here once you start chatting!
          </div>
        </SidebarGroupContent>
      </SidebarGroup>
    );
  }

  const groupSessionsByDate = (sessions: Session[]): GroupedSessions => {
    const now = new Date();
    const oneWeekAgo = subWeeks(now, 1);
    const oneMonthAgo = subMonths(now, 1);

    return sessions.reduce(
      (groups, chat) => {
        const chatDate = new Date(chat.created_at);

        if (isToday(chatDate)) {
          groups.today.push(chat);
        } else if (isYesterday(chatDate)) {
          groups.yesterday.push(chat);
        } else if (chatDate > oneWeekAgo) {
          groups.lastWeek.push(chat);
        } else if (chatDate > oneMonthAgo) {
          groups.lastMonth.push(chat);
        } else {
          groups.older.push(chat);
        }

        return groups;
      },
      {
        today: [],
        yesterday: [],
        lastWeek: [],
        lastMonth: [],
        older: [],
      } as GroupedSessions,
    );
  };

  return (
    <>
      <SidebarGroup>
        <SidebarGroupContent>
          <SidebarMenu>
            {history &&
              (() => {
                const groupedSessions = groupSessionsByDate(history);

                return (
                  <>
                    {groupedSessions.today.length > 0 && (
                      <>
                        <div className="px-2 py-1 text-xs text-sidebar-foreground/50">
                          Today
                        </div>
                        {groupedSessions.today.map((session) => (
                          <SessionItem
                            key={session.id}
                            session={session}
                            isActive={session.id === sessionId}
                            onDelete={(sessionId) => {
                              setDeleteId(sessionId);
                              setShowDeleteDialog(true);
                            }}
                            setOpenMobile={setOpenMobile}
                          />
                        ))}
                      </>
                    )}

                    {groupedSessions.yesterday.length > 0 && (
                      <>
                        <div className="px-2 py-1 text-xs text-sidebar-foreground/50 mt-6">
                          Yesterday
                        </div>
                        {groupedSessions.yesterday.map((session) => (
                          <SessionItem
                            key={session.id}
                            session={session}
                            isActive={session.id === sessionId}
                            onDelete={(sessionId) => {
                              setDeleteId(sessionId);
                              setShowDeleteDialog(true);
                            }}
                            setOpenMobile={setOpenMobile}
                          />
                        ))}
                      </>
                    )}

                    {groupedSessions.lastWeek.length > 0 && (
                      <>
                        <div className="px-2 py-1 text-xs text-sidebar-foreground/50 mt-6">
                          Last 7 days
                        </div>
                        {groupedSessions.lastWeek.map((session) => (
                          <SessionItem
                            key={session.id}
                            session={session}
                            isActive={session.id === sessionId}
                            onDelete={(sessionId) => {
                              setDeleteId(sessionId);
                              setShowDeleteDialog(true);
                            }}
                            setOpenMobile={setOpenMobile}
                          />
                        ))}
                      </>
                    )}

                    {groupedSessions.lastMonth.length > 0 && (
                      <>
                        <div className="px-2 py-1 text-xs text-sidebar-foreground/50 mt-6">
                          Last 30 days
                        </div>
                        {groupedSessions.lastMonth.map((session) => (
                          <SessionItem
                            key={session.id}
                            session={session}
                            isActive={session.id === sessionId}
                            onDelete={(sessionId) => {
                              setDeleteId(sessionId);
                              setShowDeleteDialog(true);
                            }}
                            setOpenMobile={setOpenMobile}
                          />
                        ))}
                      </>
                    )}

                    {groupedSessions.older.length > 0 && (
                      <>
                        <div className="px-2 py-1 text-xs text-sidebar-foreground/50 mt-6">
                          Older
                        </div>
                        {groupedSessions.older.map((session) => (
                          <SessionItem
                            key={session.id}
                            session={session}
                            isActive={session.id === sessionId}
                            onDelete={(sessionId) => {
                              setDeleteId(sessionId);
                              setShowDeleteDialog(true);
                            }}
                            setOpenMobile={setOpenMobile}
                          />
                        ))}
                      </>
                    )}
                  </>
                );
              })()}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>

      {/* TODO we're having this https://github.com/shadcn-ui/ui/issues/1859 */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete session?</AlertDialogTitle>
            <AlertDialogDescription>
              This will delete{" "}
              <span className="font-bold">
                {history?.filter((h) => h.id === deleteId)[0]?.title}
              </span>
              .
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>
              Continue
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
