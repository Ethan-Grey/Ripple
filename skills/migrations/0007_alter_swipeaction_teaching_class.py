# Generated manually to change SwipeAction from Skill to TeachingClass

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def clear_swipe_actions(apps, schema_editor):
    """Clear all existing SwipeAction records since we're changing the relationship"""
    SwipeAction = apps.get_model('skills', 'SwipeAction')
    SwipeAction.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('skills', '0006_merge_20251107_1106'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Clear existing swipe actions since we're changing the relationship
        migrations.RunPython(clear_swipe_actions, migrations.RunPython.noop),
        # Remove the old unique_together constraint
        migrations.AlterUniqueTogether(
            name='swipeaction',
            unique_together=set(),
        ),
        # Remove the skill field
        migrations.RemoveField(
            model_name='swipeaction',
            name='skill',
        ),
        # Add the teaching_class field
        migrations.AddField(
            model_name='swipeaction',
            name='teaching_class',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='swipe_actions',
                to='skills.teachingclass',
                null=True,  # Temporarily nullable
            ),
        ),
        # Make teaching_class non-nullable
        migrations.AlterField(
            model_name='swipeaction',
            name='teaching_class',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='swipe_actions',
                to='skills.teachingclass',
            ),
        ),
        # Add the new unique_together constraint
        migrations.AlterUniqueTogether(
            name='swipeaction',
            unique_together={('user', 'teaching_class')},
        ),
    ]

