import { API } from "../lib/api";

export async function load({ fetch }) {
  const api = new API(`http://localhost:8000`, fetch);
  return {
    api, user: api.currentUser()
  }
}
