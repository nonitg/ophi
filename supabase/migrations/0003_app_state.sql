-- What the running app reads and writes: each patient's chart (the demo's fictional cases) and the
-- workflow around it: case state, recover follow-ups and the audit trail. Replaces cases/demo/*.yaml and var/*.json
-- when SUPABASE_DB_URL is set.

create schema if not exists app;

create table if not exists app.patient_case (
  case_id     text primary key,
  chart_yaml  text not null,  -- casegen YAML, verbatim
  source      text not null,  -- where it was loaded from
  updated_at  timestamptz not null default now()
);

create table if not exists app.case_state (
  case_id     text primary key,
  state       jsonb not null,  -- service.CaseState
  updated_at  timestamptz not null default now()
);

create table if not exists app.followup (
  row_id      text primary key,
  followup    jsonb not null,  -- service.FollowUp
  updated_at  timestamptz not null default now()
);

create table if not exists app.audit_event (
  id       bigint generated always as identity primary key,
  at       timestamptz not null,
  case_id  text not null,
  actor    text not null,
  event    text not null,
  detail   text not null
);
create index if not exists audit_event_case_idx on app.audit_event (case_id, id);

alter table app.patient_case enable row level security;
alter table app.case_state enable row level security;
alter table app.followup enable row level security;
alter table app.audit_event enable row level security;

-- The app's own login (scripts/supabase-app-role.py) reads and writes; nothing is exposed to the Data API.
do $$
declare t text;
begin
  if exists (select 1 from pg_roles where rolname = 'ophi_app') then
    grant usage on schema app to ophi_app;
    grant select, insert, update, delete on all tables in schema app to ophi_app;
    for t in select tablename from pg_tables where schemaname = 'app' loop
      execute format('drop policy if exists app_all on app.%I', t);
      execute format('create policy app_all on app.%I for all to ophi_app using (true) with check (true)', t);
    end loop;
  end if;
end $$;
