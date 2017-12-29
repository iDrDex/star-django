# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0011_store_attrs_in_json'),
    ]

    operations = [
        migrations.RunSQL("""
alter table series add column tsv tsvector;

create or replace function make_attrs_tsv() returns trigger as $$
declare
  tmp text;
begin
  NEW.tsv = to_tsvector((select string_agg(value, ' ') from json_each_text(NEW.attrs::JSON)));
  return NEW;
end;
$$ language plpgsql stable;

create trigger update_tsv before insert or update on series
  for each row execute procedure make_attrs_tsv();

create index series_search_idx on series using gist(tsv);
        """,

        reverse_sql="""
drop index series_search_idx;
drop function make_attrs_tsv() cascade;
alter table series drop column tsv;
        """)
    ]
