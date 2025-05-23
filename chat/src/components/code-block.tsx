"use client";

import { useState } from "react";

// Use the intrinsic props for a `code` element, which already have optional children.
interface CodeBlockProps extends React.ComponentPropsWithoutRef<"code"> {
  inline?: boolean;
}

export function CodeBlock({
  inline = false,
  className = "",
  children,
  ...props
}: CodeBlockProps) {
  const [output] = useState<string | null>(null);
  const [tab] = useState<"code" | "run">("code");

  if (!inline) {
    return (
      <div className="not-prose flex flex-col">
        {tab === "code" && (
          <pre
            {...props}
            className={
              "text-sm w-full overflow-x-auto dark:bg-zinc-900 p-4 border border-zinc-200 dark:border-zinc-700 rounded-xl dark:text-zinc-50 text-zinc-900"
            }
          >
            <code className="whitespace-pre-wrap break-words">{children}</code>
          </pre>
        )}

        {tab === "run" && output && (
          <div className="text-sm w-full overflow-x-auto bg-zinc-800 dark:bg-zinc-900 p-4 border border-zinc-200 dark:border-zinc-700 border-t-0 rounded-b-xl text-zinc-50">
            <code>{output}</code>
          </div>
        )}
      </div>
    );
  }
  return (
    <code
      className={`${className} text-sm bg-zinc-100 dark:bg-zinc-800 py-0.5 px-1 rounded-md`}
      {...props}
    >
      {children}
    </code>
  );
}
