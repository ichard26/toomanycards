# TooManyCards (TMC)

**An overengineered Quizlet "replacement".**

So, uh, welcome to what has been my pet project for a month or so. If you came here
looking for a viable alternative to Quizlet, this is... not it. It's intended for only one
user: me! (and I have quite basic needs...)

Otherwise, enjoy my probably terrible code as TMC is also my chance to learn API design
and modern frontend development. 🌺

## License

I don't know why you'd want to reuse this code, but the project is licensed under the
[Mozilla Public License 2.0](./LICENSE.txt) just in case. Licenses of "borrowed" code
[can be found in `LICENSE-THIRDPARTY.md`](./LICENSE-THIRDPARTY.md).

## Security

The short of it is "don't trust me, I don't know what I'm doing, mostly."

The long answer [can be found in `SECURITY.md`.](./SECURITY.md)

## To-do list

- Deck creation and edit routes
- PWA support
  - Basic offline support
- ~~Public decks~~
- More modes:
  - "Flashcard" mode
  - Test mode
  - Spaced repetition mode (depends on storing results)
- Result breakdown on deck completion
- Result storage (for "these are the terms that you need to work on the most")
- Reworked UI

Lower priority:

- GitHub (and potentially Google...?) Sign-on
- Private deck sharing (à la Google Docs)
- Admin UI
- Markdown support

## API database (SQLite) schema

```sql
CREATE TABLE "users" (
    "username"         TEXT PRIMARY KEY NOT NULL,
    "hashed_password"  TEXT NOT NULL,
    "full_name"        TEXT,
    "is_admin"         INTEGER NOT NULL,
    "created_at"       TEXT NOT NULL,
);

CREATE TABLE "decks" (
    "id"               INTEGER PRIMARY KEY AUTOINCREMENT,
    "title"            TEXT NOT NULL,
    "description"      TEXT NOT NULL,
    "owner"            TEXT,
    "public"           INTEGER NOT NULL DEFAULT 0,
    "created_at"       TEXT NOT NULL,
    "accessed_at"      TEXT NOT NULL,
    FOREIGN KEY("owner") REFERENCES "users"("username")
);

CREATE TABLE "cards" (
    "id"               INTEGER PRIMARY KEY NOT NULL,
    "deck_id"          INTEGER NOT NULL,
    "term"             TEXT NOT NULL,
    "definition"       TEXT NOT NULL,
    FOREIGN KEY("deck_id") REFERENCES "decks"("id")
);

CREATE TABLE "requests" (
    "datetime"   TEXT PRIMARY KEY NOT NULL,
    "ip"         TEXT,
    "useragent"  TEXT,
    "verb"       TEXT NOT NULL,
    "path"       TEXT NOT NULL,
    "code"       INTEGER NOT NULL,
    "duration"   REAL NOT NULL
);

CREATE TABLE "sessions" (
    "username"	      TEXT NOT NULL,
    "refresh_token"	  TEXT PRIMARY KEY NOT NULL,
    "refresh_expiry"  TEXT NOT NULL,
    "access_token"    TEXT NOT NULL UNIQUE,
    "access_expiry"   TEXT NOT NULL,
    "created_at"      TEXT NOT NULL,
    FOREIGN KEY("username") REFERENCES "users"("username")
);

CREATE TABLE "ratelimits" (
    "key"       TEXT NOT NULL,
    "duration"  INTEGER NOT NULL,
    "value"     INTEGER NOT NULL,
    "expiry"    TEXT NOT NULL,
    PRIMARY KEY("key", "expiry")
);
```
