// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

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
    this.user = null;
  }

  async currentUser({ updateCache }) {
    if (this.user === null || updateCache === true) {
      this.user = await this.get("/user").catch(() => null);
    }
    return this.user;
  }
  async get(path, args) { return this.requestJSON("GET", path, args); }
  async post(path, args) { return this.requestJSON("POST", path, args); }

  async requestJSON(method, path, args = {}) {
    args.headers = { "Accept": "application/json", ...args.headers };
    return this.request(method, path, args).then((resp) => resp.json());
  }

  async request(method, path, { authenticated = true, retry = true, body, headers, priority = "auto" }) {
    // TODO: rework authentication management entirely because this is dumb and
    // wayyyy too hard to read...
    const args = { method, headers: {}, body, credentials: "include", priority };
    if (authenticated === true) {
      if (this.accessToken === null && !await this.refreshSession()) {
        return Promise.reject({ status: 401, message: "Unable to refresh session"});
      }
      args.headers["Authorization"] = `Bearer ${this.accessToken}`;
    } else if (authenticated === "if-possible") {
      // TODO: make sure this does the right thing on automatic retry...
      if (this.accessToken === null) await this.refreshSession();
      if (this.accessToken) args.headers["Authorization"] = `Bearer ${this.accessToken}`;
    }
    args.headers = { ...args.headers, ...headers }
    return this.fetch(`${this.pathPrefix}${path}`, args).then(async (resp) => {
      if (!resp.ok) {
        if (resp.status === 401 && authenticated === true && retry) {
          // If the request fails with 401, then attempt to refresh the session and retry
          // the request with (hopefully) valid credentials.
          if (await this.refreshSession()) {
            return this.request(method, path, { retry: false, body, headers })
          }
        }
        // There's nothing we can do, reject the promise.
        return Promise.reject(resp);
      }
      return resp;
    });
  }

  async refreshSession() {
    if (this._accessTokenPromise !== null) {
      return this._accessTokenPromise;
    }

    console.log("[API] %cAttempting to refresh session...", "color: gray")
    this._accessTokenPromise = this.post("/session/refresh", { authenticated: false, retry: false }).then((resp) => {
      console.log(`[API] %cAccess token acquired!`, "color: green");
      this.accessToken = resp.session.access_token;
      this.user = resp.user;
      return true;
    }).catch((reason) => {
      console.warn(`[API] Failed to acquire new access token: ${reason}`);
      this.accessToken = this.user = null;
      return false;
    }).finally(() => { this._accessTokenPromise = null; });
    return this._accessTokenPromise;
  }
}
