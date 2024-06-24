# Generated by Django 3.2.23 on 2024-02-15 12:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("api", "0032_merge_20240108_1138"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnnotationResultValidation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("is_valid", models.BooleanField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name="annotationresultvalidation",
            name="annotator",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="annotation_results_validation",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="annotationresultvalidation",
            name="result",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="validations",
                to="api.annotationresult",
            ),
        ),
        migrations.CreateModel(
            name="Detector",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="DetectorConfiguration",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("configuration", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name="detectorconfiguration",
            name="detector",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="configurations",
                to="api.detector",
            ),
        ),
        migrations.AddField(
            model_name="annotationcampaign",
            name="usage",
            field=models.IntegerField(choices=[(0, "Create"), (1, "Check")], default=0),
        ),
        migrations.AddField(
            model_name="annotationresult",
            name="annotation_campaign",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="results",
                to="api.annotationcampaign",
            ),
        ),
        migrations.AddField(
            model_name="annotationresult",
            name="annotator",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="annotation_results",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="annotationresult",
            name="dataset_file",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="annotation_results",
                to="api.datasetfile",
            ),
        ),
        migrations.AddField(
            model_name="annotationresult",
            name="detector_configuration",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="annotation_results",
                to="api.detectorconfiguration",
            ),
        ),
        migrations.RunSQL(
            """
            UPDATE annotation_results
            SET
                annotation_campaign_id=t.annotation_campaign_id,
                annotator_id=t.annotator_id,
                dataset_file_id=t.dataset_file_id
            FROM annotation_results r LEFT JOIN annotation_tasks t on t.id = r.annotation_task_id
            """
        ),
        migrations.AlterField(
            model_name="annotationresult",
            name="annotation_campaign",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="results",
                to="api.annotationcampaign",
            ),
        ),
        migrations.AlterField(
            model_name="annotationresult",
            name="dataset_file",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="annotation_results",
                to="api.datasetfile",
            ),
        ),
        migrations.RemoveField(
            model_name="collection",
            name="owner",
        ),
        migrations.RemoveField(
            model_name="tabularmetadatashape",
            name="tabular_metadata_dimension",
        ),
        migrations.RemoveField(
            model_name="tabularmetadatashape",
            name="tabular_metadata_variable",
        ),
        migrations.RemoveField(
            model_name="tabularmetadatavariable",
            name="tabular_metadata",
        ),
        migrations.RemoveField(
            model_name="annotationresult",
            name="annotation_task",
        ),
        migrations.RemoveField(
            model_name="annotationset",
            name="owner",
        ),
        migrations.RemoveField(
            model_name="dataset",
            name="collections",
        ),
        migrations.RemoveField(
            model_name="dataset",
            name="tabular_metadatum",
        ),
        migrations.RemoveField(
            model_name="datasetfile",
            name="tabular_metadatum",
        ),
        migrations.AlterField(
            model_name="confidenceindicator",
            name="label",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name="confidenceindicator",
            unique_together={("confidence_indicator_set", "label")},
        ),
        migrations.AddConstraint(
            model_name="annotationresult",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("annotator__isnull", True),
                        ("detector_configuration__isnull", False),
                    ),
                    models.Q(
                        ("annotator__isnull", False),
                        ("detector_configuration__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="require_user_or_detector",
            ),
        ),
        migrations.DeleteModel(
            name="Collection",
        ),
        migrations.DeleteModel(
            name="TabularMetadataShape",
        ),
        migrations.DeleteModel(
            name="TabularMetadataVariable",
        ),
        migrations.DeleteModel(
            name="TabularMetadatum",
        ),
    ]