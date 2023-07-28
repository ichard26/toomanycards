<script>
  export let data;
  let username, password;

  async function submitCredentials(e) {
    await data.api.post("/login", {
      authenticated: false,
      headers: {
        "X-CSRF-Protection": "1",
      },
      body: new URLSearchParams({
        "username": username,
        "password": password,
      })
    });
    username = password = null;
    document.location.href = "/";
  }
</script>

<svelte:head>
  <title>Login</title>
</svelte:head>
<h1>Login</h1>

<form action=":8000/login" method="POST">
  <input name="username" autocomplete="username" placeholder="username" bind:value={username}>
  <input name="password" autocomplete="current-password" placeholder="password" type="password" bind:value={password}>
  <button type="submit" on:click|preventDefault={submitCredentials}>Submit</button>
</form>
