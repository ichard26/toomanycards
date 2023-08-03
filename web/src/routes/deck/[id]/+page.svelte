<script>
  export let data;
  const { api, deck } = data;
</script>

<svelte:head>
  <title>{deck.name} (#{deck.id})</title>
</svelte:head>

<h1>{deck.name}</h1>
<p><b>{deck.description}</b></p>
<div class="app-div">
  <button class="difficulty-button">Difficulty: multiple-choice</button>
  <button class="pool-button">Mode: name</button>
  <p class="cards-left-text"></p>
  <div class="card-div">
    <p class="card-text">Oxygen</p>
  </div>
  <div class="selection-div"></div>
</div>
<p class="result-text"></p>
