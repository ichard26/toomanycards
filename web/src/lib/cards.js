// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

export const DEFAULT_CONFIG = {
  mode: "multiple-choice", multipleChoiceOptions: 5, removalThreshold: 1
};

export function shuffle(array) {
  let currentIndex = array.length, randomIndex;

  // While there remain elements to shuffle.
  while (currentIndex != 0) {

    // Pick a remaining element.
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex--;

    // And swap it with the current element.
    [array[currentIndex], array[randomIndex]] = [
      array[randomIndex], array[currentIndex]];
  }

  return array;
}

export function randomItem(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

export function randomSubarray(arr, size) {
  var shuffled = arr.slice(0), i = arr.length, temp, index;
  while (i--) {
    index = Math.floor((i + 1) * Math.random());
    temp = shuffled[index];
    shuffled[index] = shuffled[i];
    shuffled[i] = temp;
  }
  return shuffled.slice(0, size);
}

export class Card {
  constructor(id, term, definition, flipped = false) {
    this._id = id;
    this.term = term;
    this.definition = definition;
    this.flipped = flipped;
  }

  get front() { return !this.flipped ? this.term : this.definition; }
  get back() { return !this.flipped ? this.definition : this.term; }
  flip() { this.flipped = !this.flipped; }

  get id() { return !this.flipped ? this._id : `[F]${this._id}`; }
}

export class CardPool {
  constructor(map) {
    this.cards = new Map();
    if (map instanceof CardPool) {
      map.cards.forEach((card, term) => this.cards.set(term, card));
    } else if (map instanceof Array) {
      map.map((card) => this.cards.set(card.term, card));
    } else {
      for (const [term, def] of Object.entries(map)) {
        this.cards.set(term, new Card(term, term, def));
      }
    }
  }

  [Symbol.iterator]() { return this.cards.values(); }
  get size() { return this.cards.size; }
  get flipped() { return this.cards.values().next().value.flipped; }

  terms() { return [...this.cards.keys()]; }
  definitions() { return Array.from(this, (card) => card.definition); }
  // Treat the opposite side as the front (as if each card was flipped in the deck).
  flip() { for (const card of this) { card.flip(); } }
  // Return the backsides of all cards.
  backsides() { return Array.from(this, (card) => card.back); }
  // Search for and return a card.
  get(term) { return this.cards.get(term); }
  // Return a random card.
  getRandom() { return this.get(randomItem(this.terms())); }
  remove(card) {return this.cards.delete(card.term); }
  clone() { return new CardPool(this); }
}

export class AnswerTracker {
  constructor(removalThreshold) {
    this.removalThreshold = removalThreshold;
    this.answerRecords = new Map();
  }

  getRecord(card) { return this.answerRecords.get(card.id); }
  wrongAnswer(card, answer) { this._logAnswer(card, answer, false); }
  // Log a correct answer and return whether the card should be removed (according to the
  // removal threshold).
  correctAnswer(card, answer) {
    this._logAnswer(card, answer, true);
    return this.getRecord(card).correct >= this.removalThreshold;
  }

  // Log an answer and update the card's record.
  _logAnswer(card, answer, isCorrect) {
    if (!this.answerRecords.has(card.id)) {
      this.answerRecords.set(card.id, { card, correct: 0, wrong: 0, answers: []});
    }
    const record = this.getRecord(card);
    if (isCorrect) {
      record.correct += 1;
    } else {
      record.wrong += 1;
    }
    record.answers.push({ answer: answer, correct: isCorrect });
  }
}
