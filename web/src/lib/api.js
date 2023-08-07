/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

// Referenced resources:
// - https://stackoverflow.com/questions/38235715/fetch-reject-promise-and-catch-the-error-if-status-is-not-ok
// - https://stackoverflow.com/questions/41638553/javascript-return-a-promise-inside-async-function
// - https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Destructuring_assignment

export class API {
  constructor(pathPrefix, fetchWrapper) {
    this.pathPrefix = pathPrefix;
    if (!fetchWrapper) {
      this.fetch = fetch;
    } else {
      this.fetch = fetchWrapper;
    }
    this.accessToken = null;
    this._accessTokenPromise = null;
  }

  async currentUser(args) {
    return this.get("/current-user", args).catch(() => null);
  }
  async get(path, args) { return this.requestJSON("GET", path, args); }
  async post(path, args) { return this.requestJSON("POST", path, args); }

  async requestJSON(method, path, args = {}) {
    args.headers = { "Accept": "application/json", ...args.headers };
    return this.request(method, path, args).then((resp) => resp.json());
  }

  async request(method, path, { authenticated = true, retry = true, body, headers, priority = "auto" }) {
    const args = { method, headers: {}, body, credentials: "include", priority };
    if (authenticated) {
      if (this.accessToken === null && !await this._refreshSession()) {
        return Promise.reject({ status: 401, message: "Unable to refresh session"});
      }
      args.headers["Authorization"] = `Bearer ${this.accessToken}`;
    }
    args.headers = { ...args.headers, ...headers }
    return this.fetch(`${this.pathPrefix}${path}`, args).then(async (resp) => {
      if (!resp.ok) {
        if (resp.status === 401 && authenticated && retry) {
          // If the request fails with 401, then attempt to refresh the session and retry
          // the request with (hopefully) valid credentials.
          if (await this._refreshSession()) {
            return this.request(method, path, { retry: false, body, headers })
          }
        }
        // There's nothing we can do, reject the promise.
        return Promise.reject(resp);
      }
      return resp;
    });
  }

  async _refreshSession() {
    if (this._accessTokenPromise !== null) {
      return this._accessTokenPromise;
    }

    console.log("[API] %cAttempting to refresh session...", "color: gray")
    this._accessTokenPromise = this.post("/refresh-session", { authenticated: false, retry: false }).then((token) => {
      console.log(`[API] %cAccess token acquired!`, "color: green");
      this.accessToken = token;
      return true;
    }).catch((reason) => {
      console.warn(`[API] Failed to acquire new access token: ${reason}`);
      this.accessToken = null;
      return false;
    }).finally(() => { this._accessTokenPromise = null; });
    return this._accessTokenPromise;
  }
}
