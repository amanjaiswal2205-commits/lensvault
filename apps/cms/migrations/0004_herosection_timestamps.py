from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0003_feature"),
    ]

    operations = [
        migrations.AddField(
            model_name="herosection",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="created at"),
        ),
        migrations.AddField(
            model_name="herosection",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="updated at"),
        ),
    ]
