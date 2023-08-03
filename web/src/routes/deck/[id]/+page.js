import { error } from '@sveltejs/kit';

export async function load({ params, parent }) {
  const { api } = await parent();
  const deck = await api.get(`/deck/${params.id}`).catch((resp) => {
    if (resp.status == 401) {
      throw error(401, "not authenticated, please log in");
    }
    if (resp.status == 403 || resp.status === 404) {
      throw error(404, "deck not found, sorry!");
    }
    throw error(resp.status, "unexpected error from API")
  });
  return { params, deck };
}
