<!-- This Source Code Form is subject to the terms of the Mozilla Public
   - License, v. 2.0. If a copy of the MPL was not distributed with this
   - file, You can obtain one at https://mozilla.org/MPL/2.0/. -->

<!-- Referenced resources:

  - https://developer.mozilla.org/en-US/docs/Web/CSS/cursor
  - https://www.svgrepo.com/svg/389270/library
  - https://www.svgrepo.com/svg/532245/gear-alt
  - https://www.joomlashack.com/blog/tutorials/center-and-align-items-in-css-grid/
  - https://developer.mozilla.org/en-US/docs/Web/CSS/system-color
  - https://alvarotrigo.com/blog/sticky-navbar/
  - https://stackoverflow.com/a/56678169
  - https://developer.mozilla.org/en-US/docs/Web/CSS/grid-template-columns
  - https://bootcamp.uxdesign.cc/gradient-text-in-css-609068d3f953
  - https://stackoverflow.com/questions/76449631/render-markup-while-waiting-for-data-from-load-function-in-svelte
  - https://stackoverflow.com/questions/64219141/using-javascript-how-can-i-detect-a-keypress-event-but-not-when-the-user-is-typ
-->

<script>
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { Toaster, toast } from "svelte-sonner";
  import shortcuts from "$lib/shortcuts.js";
  import "$lib/global.css";

  export let data;
  const { api, userPromise } = data

  let user;
  onMount(() => {
    (async () => {
      user = await userPromise;
    })();
    shortcuts.register({ key: "H", callback: () => goto("/") });
    shortcuts.register({ key: "S", callback: () => goto("/settings") });
    return () => { console.log("unmounted"); };
  });

  // https://stackoverflow.com/a/57795495
  const colorSchemeMatch = window.matchMedia("(prefers-color-scheme: dark)");
  let colorScheme = colorSchemeMatch.matches ? "dark" : "light";
  colorSchemeMatch.addEventListener("change", event => {
    colorScheme = event.matches ? "dark" : "light";
  });

  async function logout() {
    toast.loading("Logging out ...");
    await api.post("/logout");
    toast.success("Goodbye!");
    document.location.reload();
  }
</script>

<header>
  <p class="header-branding">
    <span class="bold brand-text tmc-colourful-text-hover"
      class:tmc-colourful-text-always={["/settings", "/admin"].includes($page.url.pathname)}
    >TooManyCards</span>
    <span class="author-text">by&nbsp;richard&nbsp;&lt;3</span>
  </p>
  <nav class="header-navigation">
    <a href="/" class="x3-side-margin">
      <img src="/images/navbar-library.svg" alt="Home (library)">
      <span class="side-margin">Home</span>
    </a>
    <a href="/settings" class="x3-side-margin">
      <img src="/images/navbar-gear.svg" alt="Settings">
      <span class="side-margin">Settings</span>
    </a>
    {#if user?.is_admin === true}
      <a href="/admin" class="x3-side-margin">
        <img src="/images/navbar-gear.svg" alt="Admin">
        <span class="side-margin">Admin</span>
      </a>
    {/if}
  </nav>
  <div class="header-account">
    {#if user === undefined}
      <span>...loading</span>
    {:else if user !== null}
      <span class="x3-side-margin">{user.display_name} [<b>{user.username}</b>]</span>
      <button on:click={logout}>Log out</button>
    {:else}
      <a href="/login?return_to={encodeURIComponent($page.url.pathname)}" tabindex="-1">
        <button type="button" >Log in</button>
      </a>
    {/if}
  </div>
</header>

<main>
  <slot />
</main>
<Toaster closeButton richColors theme={colorScheme} position="bottom-center" />

<style>
  header {
    position: fixed;
    top: 0;
    width: 100%;
    height: 4rem;
    display: grid;
    grid-template-columns: minmax(max-content, 1fr) 1fr 1fr;
    align-items: center;
    box-shadow: 1px 2px 3px var(--darker-accent-tone);
    background-color: Canvas;
  }

  header > :where(p, div) {
    margin: 1rem;
  }

  .brand-text {
    font-size: larger;
  }
  .author-text {
    font-size: smaller;
  }

  nav, nav a, .header-account {
    display: flex;
    justify-content: center;
    align-items: center;
  }

  nav a {
    padding: 5px;
    border-radius: 5px;
    background-color: color-mix(in srgb, var(--accent-color) 5%, transparent);
    text-decoration: none;
  }
  nav a:hover {
    font-weight: bold;
  }

  .header-account {
    justify-content: flex-end;
  }

  main {
    box-sizing: border-box;
    max-width: 800px;
    margin: 60px auto 0 auto;
    padding: 20px;
  }
</style>
