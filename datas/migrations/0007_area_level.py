# Generated by Django 4.2 on 2023-04-23 13:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("datas", "0006_area_toutiaodoc_govdocwordfreq_pub_date_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="area",
            name="level",
            field=models.IntegerField(default=0),
        ),
    ]