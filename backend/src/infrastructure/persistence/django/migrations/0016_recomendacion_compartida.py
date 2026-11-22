from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('api', '0015_revocacion_sesion')]
    operations = [
        migrations.AddField(model_name='recomendacion', name='compartida',
                            field=models.BooleanField(default=False)),
    ]
