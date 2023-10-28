<!-- This Source Code Form is subject to the terms of the Mozilla Public
   - License, v. 2.0. If a copy of the MPL was not distributed with this
   - file, You can obtain one at https://mozilla.org/MPL/2.0/. -->

<svelte:options accessors={true}/>

<script>
  import { getContext, onMount } from "svelte";

  export let pressed = false;
  /** @type {(rootElement: HTMLDivElement, context: object) => any} */
  export let handler = () => null;
  export let context = undefined;

  const group = getContext("tmc-toggle-group");
  let toggleID;
  /** @type {HTMLDivElement} */
  let rootElement;
  let onRelease = () => null;

  export const toggle = () => onClick();
  export const press = () => { if (!pressed) onClick(); };
  export const release = () => { if (pressed) _onClick(); };

  function _onClick() {
    pressed = !pressed;
    if (pressed) {
      onRelease = handler(rootElement, context);
    } else {
      if (onRelease) onRelease(rootElement, context);
    }
  };

  function onClick() {
    group?.setHandlerContext(context);
    group?.reset({ except: toggleID });
    _onClick();
  };

  if (group) {
    toggleID = group.register( { release, getPressedStatus: () => pressed });
    if (group.handler)
      handler = group.handler;
  }

  onMount(() => {
    return () => group?.unregister(toggleID);
  });
</script>

<div
  class="tmc-toggle" class:pressed
  role="button" tabindex="0"
  on:click={onClick}
  on:keydown={(event) => {
    if (event.code === "Enter" || event.code === "Space") onclick();
  }}
  bind:this={rootElement}>
  <slot />
</div>

<style>
  div {
    display: contents;
  }
</style>
