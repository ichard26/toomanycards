<script>
  import { onMount } from "svelte";

  export let api;
  export let loud = false;

  let user;
  onMount(() => {
    (async () => {
      user = await api.currentUser({ priority: "low" });
    })();
  });

  async function logout() {
    await api.post("/logout");
    document.location.reload();
  }
</script>

<footer class="{loud ? 'loud' : 'quiet'}">
  {#if user === undefined}
    <p>...loading</p>
  {:else if user !== null}
    <span>Logged in as <b>{user.username} ({user.full_name})</b></span>
    <button class="link" on:click={logout}>Log out</button>
  {:else}
    <a href="/login" tabindex="-1"><button type="button" >Log in</button></a>
  {/if}
  <nav style="display: contents"><a href="/">Home</a></nav>
  <p style="font-size: smaller; margin: 0;">© 2023-present |
    Richard Si
  </p>
</footer>

<style>
  nav a {
    font-weight: bold;
  }
  footer {
    padding: 10px 2em;
    margin: auto;
    margin-bottom: 20px;
    font-size: 0.9em;
  }
  footer.quiet {
    filter: opacity(80%);
  }
  footer.quiet:hover {
    filter: opacity(100%);
    transition: ease-in-out 200ms;
  }
  footer.loud {
    background-color: rgb(255, 192, 203, 0.1);
    border: 2px pink solid;
    border-radius: 6px;
    box-shadow: 2px 4px pink;
  }
  footer button {
    margin: 0 10px;
    margin-bottom: 0.5rem;
    font-weight: bold;
  }
  @media (max-width: 400px) {
    footer button {
      margin-top: 0.4rem;
      margin-bottom: 1rem;
    }
  }
</style>
