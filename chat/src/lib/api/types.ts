import type { components } from "./v1";

// TODO should be replaced with SDK type
export type User = {
  id: string;
  name: string;
  avatar?: string;
  email: string;
};

export type Session = components["schemas"]["SessionDTO"];
