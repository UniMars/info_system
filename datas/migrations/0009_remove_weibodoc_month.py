# Generated by Django 4.2 on 2023-04-24 21:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("datas", "0008_weibodoc_alter_area_name"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="weibodoc",
            name="month",
        ),
    ]
