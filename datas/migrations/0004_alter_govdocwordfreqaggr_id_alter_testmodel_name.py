# Generated by Django 4.2 on 2023-04-08 22:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("datas", "0003_alter_govdocwordfreq_word_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="govdocwordfreqaggr",
            name="id",
            field=models.BigAutoField(
                editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="govdocwordfreqaggr",
            name="freq",
            field=models.IntegerField(default=0),

        ),
        migrations.AlterField(
            model_name="testmodel",
            name="name",
            field=models.CharField(default="test_name", max_length=50),
        ),
    ]
