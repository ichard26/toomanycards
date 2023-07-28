<script>
  export let api;
  export let userPromise;
  // const userPromise = api.currentUser();

  async function logout() {
    await api.post("/logout");
    document.location.reload();
  }
</script>

<header>
  {#await userPromise}
    <span>...loading</span>
  {:then user}
    {#if user !== null}
      <span>Logged in as <b>{user.username} ({user.full_name})</b></span>
      <button on:click={logout}>Log out</button>
    {:else}
      <a href="login" tabindex="-1"><button type="button">Log in</button></a>
    {/if}
  {/await}
  <a href="test">test</a>
  <a href="/">home</a>
</header>

<style>
  header {
    padding: 10px;
    margin: 10px 0;

    background-color: rgb(255, 192, 203, 0.1);
    border: 2px pink solid;
    border-radius: 6px;
    box-shadow: 2px 4px pink;
  }
  header button {
    margin: 0 10px;
  }
</style>
