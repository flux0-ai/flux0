import createFetchClient from "openapi-fetch";
import createClient from "openapi-react-query";
import type { paths } from "./v1";

export type APIError = {
  detail: string | string[];
};

const customFetch: typeof fetch = async (input, init) => {
  const response = await fetch(input, init);

  if (!response.ok) {
    // Reject the promise if the response is not OK (4xx or 5xx)
    const errorBody = await response.json();
    const error: APIError = {
      detail: errorBody.detail || "An error occurred",
    };
    throw error;
  }

  return response;
};

export const fetchClientWithThrow = createFetchClient<paths>({
  baseUrl: "/",
  fetch: customFetch,
});

export const fetchClient = createFetchClient<paths>({
  baseUrl: "/",
});

export const $api = createClient(fetchClient);
