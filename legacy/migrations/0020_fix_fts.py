# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0019_update_platform_fields'),
    ]

    operations = [
        migrations.RunSQL("""
create or replace function make_attrs_tsv() returns trigger as $$
declare
  tmp text;
begin
  NEW.tsv = to_tsvector('english', (select string_agg(value, ' ') from json_each_text(NEW.attrs::JSON)));
  return NEW;
end;
$$ language plpgsql stable;

update series set id=id;  -- recalc tsv
        """)
    ]
