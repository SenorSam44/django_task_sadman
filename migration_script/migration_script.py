from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    indexes = [
        ('start_time', 'appt_start_idx', 'Index for date range queries in reports'),
        ('provider', 'appt_provider_idx', 'Index for group by provider in analytics'),
        ('service', 'appt_service_idx', 'Index for group by service'),
        (['booking_system', 'start_time'], 'appt_bs_start_idx', 'Composite index for filtered date ranges per system'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=fields, name=name),
        )
        for fields, name, _comment in indexes
    ]