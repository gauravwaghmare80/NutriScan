# Generated by Django 5.1.5 on 2025-02-17 15:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('age', models.IntegerField()),
                ('weight', models.FloatField()),
                ('height', models.FloatField()),
                ('activity_level', models.CharField(choices=[('sedentary', 'Sedentary'), ('lightly_active', 'Lightly Active'), ('moderately_active', 'Moderately Active'), ('very_active', 'Very Active')], max_length=50)),
                ('goal', models.CharField(choices=[('weight_loss', 'Weight Loss'), ('muscle_gain', 'Muscle Gain'), ('maintenance', 'Maintenance')], max_length=50)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
