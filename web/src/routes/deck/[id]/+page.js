import { error } from '@sveltejs/kit';

export async function load({ params, parent }) {
  const { api } = await parent();
  const deck = await api.get(`/deck/${params.id}`).catch((resp) => {
    if (resp.status == 401 || resp.status == 403 || resp.status === 404) {
      throw error(404, "deck not found, sorry!");
    }
  });
  return { params, deck };
}
