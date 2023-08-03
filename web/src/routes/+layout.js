import { API } from "../lib/api";

export const ssr = false;

export async function load({ fetch }) {
  return {
    api: new API("/api", fetch)
  };
}
