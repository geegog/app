drop table if exists users;
create table users (
  id integer primary key autoincrement,
  first_name text not null,
  last_name text not null,
  email text not null unique,
  password text not null,
  phone_number text not null,
  file_name text null
);

drop table if exists logs;
create table logs (
  id integer primary key autoincrement,
  email text not null,
  action text not null,
  time date_time not null
);