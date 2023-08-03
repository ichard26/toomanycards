<script>
  import Footer from "../lib/components/footer.svelte";
  import { page } from "$app/stores";
  export let data;
</script>

<main>
  <slot />
</main>
<Footer api={data.api} loud={$page.route.id == "/"}/>
