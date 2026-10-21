from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("expenses", "0004_category_order_is_shown"),
        ("services", "0008_add_icons"),
    ]

    operations = [
        migrations.AddField(
            model_name="servicecategory",
            name="expense_category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="service_categories",
                to="expenses.expensecategory",
            ),
        ),
    ]
