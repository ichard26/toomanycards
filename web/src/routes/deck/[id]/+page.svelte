<script>
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
  let currentCard = null;
  let trackNextAnswer = true;
  let cardsLeft = pool.size;
  let resultMessage = "";

  const onButtonSubmit = (event) => {
    event.target.setCustomValidity("");
    if (event.key === "Enter") {
      if (!event.target.value.length) {
        event.target.setCustomValidity("You cannot enter a blank answer.");
        event.target.reportValidity();
        return;
      }
      submitAnswer(event.target.value, { log: trackNextAnswer });
      event.target.value = "";
    }
  }
  let options = null;

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
    pool = originalPool.clone();
    answerTracker = new AnswerTracker(config.removalThreshold);
  }

  if (cardsLeft) dealCard();
  window.submitAnswer = submitAnswer;
</script>

<svelte:head>
  <title>{deck.name} (#{deck.id})</title>
</svelte:head>

<h1>{deck.name}</h1>
<p><b>{deck.description}</b></p>
<button on:click={() => {
  difficulty = (difficulty === "exact-answer" ? "multiple-choice" : "exact-answer");
  dealCard();
}}>Difficulty: {difficulty}</button>
<button on:click={() => {
  pool.flip();
  mode = pool.flipped ? "term" : "definition";
  dealCard();
}}>Mode: {mode}</button>
<p>{cardsLeft}/{originalPool.size} cards left</p>

{#if cardsLeft === 0}
  {#if originalPool.size === 0}
    <p class="card-text">empty deck, sorry</p>
  {:else}
    <p class="card-text">deck finished!&nbsp;🎉</p>
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
      <input on:keydown={onButtonSubmit} autofocus>
      <button id="submit-button" on:click={onButtonSubmit}>Submit</button>
    {/if}
  </div>
{/if}

<p>{resultMessage}</p>

<style>
.card-text {
  color: var(--primary-accent-color);
  font-size: 3em;
  font-weight: bold;
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
