# Generated by Django 5.0.6 on 2024-05-10 21:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_company_image_remove_user_social_links_social_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.IntegerField(default=3),
        ),
    ]
