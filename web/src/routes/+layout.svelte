<!-- This Source Code Form is subject to the terms of the Mozilla Public
   - License, v. 2.0. If a copy of the MPL was not distributed with this
   - file, You can obtain one at https://mozilla.org/MPL/2.0/. -->

<script>
  import Footer from "../lib/components/footer.svelte";
  import { page } from "$app/stores";
  export let data;
</script>

<main>
  <slot />
</main>
<Footer api={data.api} loud={$page.route.id == "/"}/>
