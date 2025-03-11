import createFetchClient from "openapi-fetch";
import createClient from "openapi-react-query";
import type { paths } from "./v1";

const customFetch: typeof fetch = async (input, init) => {
  const response = await fetch(input, init);

  if (!response.ok) {
    // Reject the promise if the response is not OK (4xx or 5xx)
    const errorBody = await response.text(); // Or `response.json()` if it's JSON
    throw new Error(`HTTP ${response.status}: ${errorBody}`);
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
