# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0023_series_specie'),
    ]

    operations = [
        migrations.AddField(
            model_name='series',
            name='platforms',
            field=django.contrib.postgres.fields.ArrayField(size=None, base_field=models.CharField(max_length=127), blank=True, null=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='series',
            name='samples_count',
            field=models.IntegerField(default=0),
        ),
        migrations.RunSQL("""
create or replace function array_uniq(anyarray) returns anyarray as $$
    select array(select distinct unnest($1))
$$ language sql immutable strict;

create aggregate array_concat (
sfunc = array_cat,
basetype = anyarray,
stype = anyarray,
initcond = '{}'
);

create aggregate array_concat_uniq (
sfunc = array_cat,
finalfunc = array_uniq,
basetype = anyarray,
stype = anyarray,
initcond = '{}'
);
"""),
    ]
