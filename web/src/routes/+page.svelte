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
