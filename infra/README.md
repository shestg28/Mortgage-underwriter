Postgres local development
--------------------------

Run Postgres and pgAdmin locally for development using Docker Compose:

```sh
docker compose up -d
```

Default credentials are in `infra/env.example`.

Postgres will mount data at `infra/pgdata` and initialize with files in `infra/initdb` on first run.
