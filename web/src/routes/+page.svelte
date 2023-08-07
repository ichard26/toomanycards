<!-- This Source Code Form is subject to the terms of the Mozilla Public
   - License, v. 2.0. If a copy of the MPL was not distributed with this
   - file, You can obtain one at https://mozilla.org/MPL/2.0/. -->

<script>
  import { onMount } from "svelte";

  export let data;
  window.api = data.api;

  let decks;
  onMount(() => {
    (async () => {
      decks = await data.api.get("/deck/library");
    })();
  });
</script>

<svelte:head>
  <title>TooManyCards</title>
</svelte:head>
<h1>TooManyCards</h1>

<p>An overengineered Quizlet "replacement".</p>

<h2>Library</h2>
{#if decks !== undefined}
  {#each decks as d}
    <a href="/deck/{d.id}"><span><b>{d.name}</b></span></a>
    <br>
    <span>{d.description} ({d.cards.length} cards)</span>
    <br>
    <br>
  {/each}
{/if}
