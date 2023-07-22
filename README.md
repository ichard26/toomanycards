# TooManyCards (TMC)

**An overengineered Quizlet "replacement".**

So, uh, welcome to what has been my pet project for a month or so. If you came here
looking for a viable alternative to Quizlet, this is... not it. It's intended for only one
user: me! (and I have quite basic needs...)

Otherwise, enjoy my probably terrible code as TMC is also my chance to learn API design
and modern frontend development. 🌺

## Security

The short of it is "don't trust me, I don't know what I'm doing, mostly."

The long answer [can be found in `SECURITY.md`.](./SECURITY.md)

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
    "created_at"       TEXT NOT NULL,
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
    "duration"   REAL NOT NULL,
) WITHOUT ROWID;

CREATE TABLE "sessions" (
    "id"            TEXT PRIMARY KEY NOT NULL,
    "username"      TEXT NOT NULL,
    "created_at"    TEXT NOT NULL,
    "expired_at"    TEXT NOT NULL,
    FOREIGN KEY("username") REFERENCES "users"("username")
) WITHOUT ROWID;

CREATE TABLE "ratelimits" (
    "key"       TEXT NOT NULL,
     "duration"  INTEGER NOT NULL,
     "value"     INTEGER NOT NULL,
     "expiry"    TEXT NOT NULL,
     PRIMARY KEY("key", "expiry")
);
```
