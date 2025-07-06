CREATE TABLE BaseStations (
    id         SERIAL PRIMARY KEY,
    sitename   TEXT   NOT NULL UNIQUE,
    city       TEXT   NOT NULL,
    topic_id   INTEGER,
    width      TEXT,
    length     TEXT,
);

CREATE TABLE Tasks (
    id                 SERIAL PRIMARY KEY,
    tasknum            TEXT      NOT NULL,
    basestation        TEXT      NOT NULL,
    status             TEXT      NOT NULL,
    worker             TEXT,
    datetime           TIMESTAMP NOT NULL,
    datetimereq        TIMESTAMP,
    datetimeacc        TIMESTAMP,
    datetimeclose      TIMESTAMP,
    work_type          TEXT,
    description        TEXT,
    short_description  TEXT,
    comments           TEXT,
    adress             TEXT,
    responsible_person TEXT,
    exited_by_worker   TIMESTAMP,
    close_code         TEXT[],
    quantity           INTEGER[]
);

CREATE TABLE Workers (
    id           SERIAL PRIMARY KEY,
    tgId         TEXT   NOT NULL,
    workerFIO    TEXT     NOT NULL,
    phoneNumber  TEXT,
    City         TEXT,
    Position     TEXT
);

CREATE TABLE sent_messages (
    id            SERIAL    PRIMARY KEY,
    task_number   TEXT,
    chat_id       BIGINT,
    message_id    BIGINT    UNIQUE,
    sent_to_topic TEXT
);