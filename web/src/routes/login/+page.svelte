<!-- This Source Code Form is subject to the terms of the Mozilla Public
   - License, v. 2.0. If a copy of the MPL was not distributed with this
   - file, You can obtain one at https://mozilla.org/MPL/2.0/. -->

<script>
  export let data;
  let username, password;
  let message = "";

  async function submitCredentials(e) {
    data.api.post("/login", {
      authenticated: false,
      headers: {
        "X-CSRF-Protection": "1",
      },
      body: new URLSearchParams({
        "username": username,
        "password": password,
      })
    }).then(() => {
      message = "Success! 🎉";
      const returnTo = new URL(location.href).searchParams.get("return_to");
      if (returnTo) {
        document.location.href = decodeURIComponent(returnTo);
      } else {
        document.location.href = "/";
      }
    }).catch((resp) => {
      if (resp.status == 401) { message = "Incorrect username or password, please try again."; }
      else {
        console.error(resp);
        message = "Internal error: unable to login. Please try again later.";
      }
    }).finally(() => {
      username = password = null;
    });
  }
</script>

<svelte:head>
  <title>Login</title>
</svelte:head>
<div>

<h1>Login</h1>

<form action="/api/login" method="POST">
  <!-- svelte-ignore a11y-autofocus -->
  <input name="username" autocomplete="username" placeholder="username" bind:value={username} autofocus>
  <input name="password" autocomplete="current-password" placeholder="password" type="password" bind:value={password}>
  <p><button type="submit" on:click|preventDefault={submitCredentials}>Submit</button></p>
</form>
<p>{message}</p>
</div>

<style>
  div, form {
    display: grid;
    justify-items: center;
  }
  input {
    max-width: 300px;
    padding: 0.8em;
  }
  button {
    padding: 0.5em;
  }
</style>
