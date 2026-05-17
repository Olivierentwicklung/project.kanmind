from rest_framework import serializers

from auth_app.models import UserProfile
from kanban_app.tasks.models import Task


class TaskUserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'email',
            'fullname',
        ]


class TaskSerializer(serializers.ModelSerializer):
    assignee = TaskUserProfileSerializer(read_only=True)
    reviewer = TaskUserProfileSerializer(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id',
            'board',
            'title',
            'description',
            'status',
            'priority',
            'assignee',
            'reviewer',
            'due_date',
            'comments_count',
        ]
