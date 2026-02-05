# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='unit_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('minutes', 'Minutes'),
                    ('hours', 'Hours'),
                    ('count', 'Count (repetitions)'),
                ],
                help_text='Type of unit for measuring the goal (time or count)',
                max_length=20,
                null=True,
                verbose_name='unit type',
            ),
        ),
        migrations.AddField(
            model_name='task',
            name='target_value',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Target value in the specified unit (e.g., 30 minutes, 2 hours, 50 reps)',
                null=True,
                verbose_name='target value',
            ),
        ),
    ]



