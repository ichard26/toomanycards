// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

import { API } from "../lib/api";

export const ssr = false;

export async function load({ fetch }) {
  const api = new API("/api", fetch);
  return {
    api: api,
    userPromise: api.currentUser({ priority: "low" }),
  };
}
