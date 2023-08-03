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
    <span>...loading</span>
  {:else if user !== null}
    <span>Logged in as <b>{user.username} ({user.full_name})</b></span>
    <button on:click={logout}>Log out</button>
  {:else}
    <a href="/login" tabindex="-1"><button type="button">Log in</button></a>
  {/if}
  <a href="/">Home</a>
</footer>

<style>
  footer {
    padding: 10px 2em;
    margin: auto;
    margin-bottom: 20px;
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
  }
</style>
