<!-- This Source Code Form is subject to the terms of the Mozilla Public
   - License, v. 2.0. If a copy of the MPL was not distributed with this
   - file, You can obtain one at https://mozilla.org/MPL/2.0/. -->

<script>
  import { onMount } from "svelte";
  import { browser } from "$app/environment";
  import {
      DEFAULT_CONFIG as config,
      AnswerTracker,
      Card,
      CardPool,
      randomSubarray,
      shuffle,
  } from "$lib/cards.js";

  export let data;
  const { deck } = data;

  const cards = deck.cards.map((c) => new Card(c.id, c.term, c.definition));
  const originalPool = new CardPool(cards);
  let pool = originalPool.clone();
  let answerTracker = new AnswerTracker(config.removalThreshold);

  let difficulty = config.mode;
  let mode = "term";
  let currentCard = { front: "" };
  let trackNextAnswer = true;
  let cardsLeft = pool.size;
  let resultMessage = "";

  onMount(() => {
    let v;
    if ((v = localStorage.getItem("tmc-app-difficulty")) !== null) {
      difficulty = v;
    }
    if ((v = localStorage.getItem("tmc-app-mode")) !== null) {
      mode = v;
      if (mode !== "term") pool.flip();
    }
    dealCard();
    document.onkeydown = (event) => {
      if (event.key === "R" && event.altKey && event.shiftKey) {
        reset();
      }
    };
  });

  const onExactSubmit = (element) => {
    if (!element.value.length) {
      element.setCustomValidity("You cannot enter a blank answer.");
      element.reportValidity();
      return;
    }
    submitAnswer(element.value, { log: trackNextAnswer });
    element.value = "";
  }
  let options = [];
  let inputElement;

  console.log(`%cApp set up! Number of cards: ${originalPool.size}`, "font-weight: bold;");

  function dealCard({ forceCard = null } = {}) {
    resultMessage = "";
    cardsLeft = pool.size;

    currentCard = (forceCard === null ? pool.getRandom() : forceCard);
    if (currentCard === undefined) {
      console.log("No more cards left!");
      return;
    }
    const { front, back } = currentCard;
    console.log(`Selected card: ${front} -> ${back} (forced: ${!!forceCard})`);

    if (forceCard !== null) resultMessage = `Repeat answer (${back}) to continue.`;
    trackNextAnswer = !forceCard;

    if (difficulty === "multiple-choice") {
      const filtered = pool.backsides().filter(s => s !== back);
      options = shuffle(
        [...randomSubarray(filtered, config.multipleChoiceOptions - 1), back]
      );
    }
  }

  function submitAnswer(value, { log = true } = {}) {
    // When a wrong answer is submitted, the card is replayed and the correct answer must be
    // submitted before moving on to a new card. This is great, however, these "learn-from
    // -mistakes" answers shouldn't be treated a real answer (and potentially cause a card to be
    // removed). This is why `shouldLog` exists.
    const card = currentCard;
    const answer = value.trim();
    if (answer.toLowerCase() === card.back.toLowerCase()) {
      if (log && answerTracker.correctAnswer(card, answer)) {
        pool.remove(card);
        console.log(`Removed card from pool (${pool.size} left)`);
      }
      resultMessage = "Correct! 🎉"
      setTimeout(dealCard, 1000);
    } else {
      if (log) answerTracker.wrongAnswer(card, answer);
      resultMessage = `Incorrect. It was "${card.back}"`;
      setTimeout(dealCard, 1000, { forceCard: card });
    }
  }

  function reset() {
    console.log("Resetting...")
    pool = originalPool.clone();
    answerTracker = new AnswerTracker(config.removalThreshold);
    dealCard();
  }

  if (browser) {
    window.submitAnswer = submitAnswer;  // For debugging only.
    const normalizeCharacter = (c) => {
      if (c.match(/[a-z0-9\-]/)) { return c; }
      else if (c.match(/[\(\)]/)) { return ""; }
      else { return "-"; }
    };
    // Regex trick to remove consecutive duplicates: https://stackoverflow.com/a/55636681
    const normalizedName = [...deck.name.toLowerCase()].map(normalizeCharacter)
                             .join("").replace(/(.)\1+/g, "$1");
    const url = new URL(window.location.href)
    const URLPrefix = url.pathname.split("/").slice(0, -1).join("/")
    url.pathname = `${URLPrefix}/${deck.id}:${normalizedName}`;
    window.history.replaceState(null, "", url);
  }
</script>

<svelte:head>
  <title>{deck.name} (#{deck.id})</title>
</svelte:head>

<h1>{deck.name}</h1>
<p><b>{deck.description}</b></p>
<div class="knobs">
  <button on:click={() => {
    difficulty = (difficulty === "exact-answer" ? "multiple-choice" : "exact-answer");
    if (browser) localStorage.setItem("tmc-app-difficulty", difficulty);
    dealCard();
  }}>Difficulty: {difficulty}</button>
  <button on:click={() => {
    pool.flip();
    mode = pool.flipped ? "definition" : "term";
    if (browser) localStorage.setItem("tmc-app-mode", mode);
    dealCard();
  }}>Mode: {mode}</button>
</div>
<p>{cardsLeft}/{originalPool.size} cards left</p>
{#if cardsLeft === 0}
  {#if originalPool.size === 0}
    <p class="card-text">empty deck, sorry</p>
  {:else}
    <p class="card-text">deck finished!&nbsp;🎉</p>
    <button on:click={reset}>Reset</button>
  {/if}
{:else}
  <div>
    <p class="card-text">{currentCard.front}</p>
  </div>
  <div class="selection-div">
    {#if difficulty === "multiple-choice"}
      {#each options as o}
        <button on:click={submitAnswer(o, { log: trackNextAnswer })}>{o}</button>
      {/each}
    {:else if difficulty === "exact-answer"}
      <!-- svelte-ignore a11y-autofocus -->
      <input bind:this={inputElement} on:keydown={(event) => {
          event.target.setCustomValidity("");
          if (event.key === "Enter") onExactSubmit(event.target);
        }} autofocus>
      <button id="submit-button" on:click={onExactSubmit(inputElement)}>Submit</button>
    {/if}
  </div>
{/if}

<p>{resultMessage}</p>

<style>
* {
  text-align: center;
}
.card-text {
  color: var(--primary-accent-color);
  font-size: 3em;
  font-weight: bold;
}

div.knobs button {
  --color: ButtonText;
  --background-color: ButtonFace;
}

.selection-div button {
  min-width: 15%;
  min-height: 3em;
  margin: 10px 5px;
}

.selection-div input {
  box-sizing: border-box;
  max-width: 300px;
}

.selection-div input, .selection-div #submit-button {
  padding: 0.8em;
}
</style>
