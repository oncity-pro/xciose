# Generated manually for BucketDepositConfig model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_customer_total_water_usage'),
    ]

    operations = [
        migrations.CreateModel(
            name='BucketDepositConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_per_bucket', models.DecimalField(decimal_places=2, default=30.0, max_digits=10, verbose_name='每桶押金金额')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '空桶押金配置',
                'verbose_name_plural': '空桶押金配置',
            },
        ),
    ]
