# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '__first__'),
        ('tags', '0005_userstats'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('samples', models.IntegerField()),
                ('amount', models.DecimalField(max_digits=8, decimal_places=2)),
                ('method', models.TextField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(to='legacy.AuthUser')),
                ('receiver', models.ForeignKey(related_name='payments', to='legacy.AuthUser')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='userstats',
            name='user',
            field=models.OneToOneField(related_name='stats', primary_key=True, serialize=False, to='legacy.AuthUser'),
            preserve_default=True,
        ),
    ]
