// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

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
