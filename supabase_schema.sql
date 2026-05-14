create table if not exists scrape_results (
  id bigserial primary key,
  website text not null,
  role text not null,
  full_name text not null,
  created_at timestamptz not null default now()
);

create table if not exists scrape_failed (
  id bigserial primary key,
  website text not null,
  created_at timestamptz not null default now()
);
