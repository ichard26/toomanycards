// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import BuildInfo from "vite-plugin-info";

export default defineConfig({
    plugins: [sveltekit(), BuildInfo()]
});
