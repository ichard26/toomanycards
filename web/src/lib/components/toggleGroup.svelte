<!-- This Source Code Form is subject to the terms of the Mozilla Public
   - License, v. 2.0. If a copy of the MPL was not distributed with this
   - file, You can obtain one at https://mozilla.org/MPL/2.0/. -->

<script>
  import { setContext } from "svelte";

  /** @type {(rootElement: HTMLDivElement, context: object) => any} */
  export let handler = null;
  export const toggles = new Map();
  export let context = {}
  let toggleID = 0;

  export function register(context) {
    toggleID += 1;
    toggles.set(toggleID, context);
    return toggleID;
  }

  export function unregister(toggleID) {
    return toggles.delete(toggleID);
  }

  export function setHandlerContext(newContext) {
    context = newContext;
  }

  export function reset({ except = null }) {
    toggles.forEach((toggle, toggleID) => {
      if (toggleID !== except && toggle.getPressedStatus()) toggle.release();
    });
  }

  setContext("tmc-toggle-group", {
    handler, setHandlerContext,
    register, unregister, reset,
  });
</script>

<slot />
