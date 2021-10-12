"""User DRF-Viewset file"""

from datetime import datetime

from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils.http import urlquote
from django.db.models import F

from rest_framework import viewsets, serializers
from rest_framework.response import Response
from rest_framework.decorators import action

from drf_spectacular.utils import extend_schema, extend_schema_field

from backend.api.models import AnnotationCampaign, AnnotationTask, AnnotationResult, SpectroConfig
from backend.settings import STATIC_URL

class AnnotationTaskSerializer(serializers.ModelSerializer):
    filename = serializers.CharField(source='dataset_file.filename')
    dataset_name = serializers.CharField(source='dataset_file.dataset.name')
    start = serializers.DateTimeField(source='dataset_file.audio_metadatum.start')
    end = serializers.DateTimeField(source='dataset_file.audio_metadatum.end')

    class Meta:
        model = AnnotationTask
        fields = ['id', 'status', 'filename', 'dataset_name', 'start', 'end']


class AnnotationTaskBoundarySerializer(serializers.Serializer):
    startTime = serializers.DateTimeField()
    endTime = serializers.DateTimeField()
    startFrequency = serializers.FloatField()
    endFrequency = serializers.FloatField()


class AnnotationTaskResultSerializer(serializers.ModelSerializer):
    annotation = serializers.CharField(source='annotation_tag.name')
    startTime = serializers.FloatField(source='start_time')
    endTime = serializers.FloatField(source='end_time')
    startFrequency = serializers.FloatField(source='start_frequency')
    endFrequency = serializers.FloatField(source='end_frequency')

    class Meta:
        model = AnnotationResult
        fields = ['id', 'annotation', 'startTime', 'endTime', 'startFrequency', 'endFrequency']


class AnnotationTaskSpectroSerializer(serializers.ModelSerializer):
    winsize = serializers.IntegerField(source='window_size')
    urls = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        if 'sound_name' in kwargs:
            self.sound_name = kwargs.pop('sound_name')
        if 'root_url' in kwargs:
            self.root_url = kwargs.pop('root_url')
        super().__init__(*args, **kwargs)

    class Meta:
        model = SpectroConfig
        fields = ['nfft', 'winsize', 'overlap', 'urls']

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_urls(self, spectro_config):
        return [
            urlquote(f'{self.root_url}/spectrograms/{spectro_config.name}/{self.sound_name}/{tile}')
            for tile in spectro_config.zoom_tiles(self.sound_name)
        ]


class AnnotationTaskRetrieveSerializer(serializers.Serializer):
    campaignId = serializers.IntegerField(source='annotation_campaign_id')
    annotationTags = serializers.SerializerMethodField()
    boundaries = serializers.SerializerMethodField()
    audioUrl = serializers.SerializerMethodField()
    audioRate = serializers.SerializerMethodField()
    spectroUrls = serializers.SerializerMethodField()
    prevAnnotations = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_annotationTags(self, task):
        return list(task.annotation_campaign.annotation_set.tags.values_list('name', flat=True))

    @extend_schema_field(AnnotationTaskBoundarySerializer)
    def get_boundaries(self, task):
        return {
            'startTime': task.dataset_file.audio_metadatum.start,
            'endTime': task.dataset_file.audio_metadatum.end,
            'startFrequency': 0,
            'endFrequency': self.get_audioRate(task) / 2
        }

    def get_audioUrl(self, task):
        root_url = STATIC_URL + task.dataset_file.dataset.dataset_path
        return f'{root_url}/{task.dataset_file.filepath}'

    @extend_schema_field(serializers.IntegerField())
    def get_audioRate(self, task):
        df_sample_rate = task.dataset_file.audio_metadatum.sample_rate_khz
        ds_sample_rate = task.dataset_file.dataset.audio_metadatum.sample_rate_khz
        sample_rate = df_sample_rate if df_sample_rate else ds_sample_rate
        return sample_rate

    @extend_schema_field(AnnotationTaskSpectroSerializer(many=True))
    def get_spectroUrls(self, task):
        root_url = STATIC_URL + task.dataset_file.dataset.dataset_path
        sound_name = task.dataset_file.filepath.split('/')[-1].replace('.wav', '')
        spectros_configs = set(task.dataset_file.dataset.spectro_configs.all()) & set(task.annotation_campaign.spectro_configs.all())
        return AnnotationTaskSpectroSerializer(spectros_configs, many=True, root_url=root_url, sound_name=sound_name).data

    @extend_schema_field(AnnotationTaskResultSerializer(many=True))
    def get_prevAnnotations(self, task):
        queryset = task.results.prefetch_related('annotation_tag')
        return AnnotationTaskResultSerializer(queryset, many=True).data


class AnnotationTaskUpdateSerializer(serializers.Serializer):
    annotations = AnnotationTaskResultSerializer(many=True)
    task_start_time = serializers.IntegerField()
    task_end_time = serializers.IntegerField()

    def update(self, task, validated_data):
        tags = dict(map(reversed, task.annotation_campaign.annotation_set.tags.values_list('id', 'name')))
        for annotation in validated_data['annotations']:
            annotation['annotation_tag_id'] = tags[annotation.pop('annotation_tag')['name']]
            task.results.create(**annotation)
        task.sessions.create(
            start=datetime.fromtimestamp(validated_data['task_start_time']),
            end=datetime.fromtimestamp(validated_data['task_end_time']),
            session_output=validated_data
        )
        task.status = 2
        task.save()
        return task


class AnnotationTaskUpdateOutputCampaignSerializer(serializers.Serializer):
    next_task = serializers.IntegerField(allow_null=True)
    campaign_id = serializers.IntegerField(allow_null=True)


class AnnotationTaskViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for annotation tasks related actions
    """

    serializer_class = AnnotationTaskSerializer

    @extend_schema(responses=AnnotationTaskSerializer(many=True))
    @action(detail=False, url_path='campaign/(?P<campaign_id>[^/.]+)')
    def campaign_list(self, request, campaign_id):
        """List tasks for given annotation campaign"""
        get_object_or_404(AnnotationCampaign, pk=campaign_id)
        queryset = AnnotationTask.objects.filter(
            annotator_id=request.user.id,
            annotation_campaign_id=campaign_id
        ).prefetch_related('dataset_file', 'dataset_file__dataset', 'dataset_file__audio_metadatum')
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(responses=AnnotationTaskRetrieveSerializer)
    def retrieve(self, request, pk):
        """Retrieve annotation task instructions to the corresponding id"""
        queryset = AnnotationTask.objects.prefetch_related(
            'annotation_campaign',
            'annotation_campaign__spectro_configs',
            'annotation_campaign__annotation_set',
            'dataset_file__audio_metadatum',
            'dataset_file__dataset',
            'dataset_file__dataset__spectro_configs',
            'dataset_file__dataset__audio_metadatum'
        )
        task = get_object_or_404(queryset, pk=pk)
        serializer = AnnotationTaskRetrieveSerializer(task)
        return Response(serializer.data)

    @extend_schema(request=AnnotationTaskUpdateSerializer, responses=AnnotationTaskUpdateOutputCampaignSerializer)
    def update(self, request, pk):
        """Update an annotation task with new results"""
        queryset = AnnotationTask.objects.filter(annotator=request.user.id)
        task = get_object_or_404(queryset, pk=pk)
        update_serializer = AnnotationTaskUpdateSerializer(task, data=request.data)
        update_serializer.is_valid(raise_exception=True)
        task = update_serializer.save()

        next_task = AnnotationTask.objects.filter(
            annotator_id=request.user.id,
            annotation_campaign_id=task.annotation_campaign_id
        ).exclude(status=2).order_by('dataset_file__audio_metadatum__start').first()
        if next_task is None:
            return Response({'next_task': None, 'campaign_id': task.annotation_campaign_id})
        return Response({'next_task': next_task.id, 'campaign_id': None})