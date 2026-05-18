from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

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


class TaskCreateSerializer(serializers.ModelSerializer):
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        source='assignee',
        required=False,
        allow_null=True,
    )

    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        source='reviewer',
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Task
        fields = [
            'id',
            'board',
            'title',
            'description',
            'status',
            'priority',
            'assignee_id',
            'reviewer_id',
            'due_date',
        ]

    def validate(self, attrs):
        request = self.context['request']
        user_profile = request.user.userprofile
        board = attrs.get('board')

        if board is None:
            return attrs

        if not (
            board.owner == user_profile
            or board.members.filter(id=user_profile.id).exists()
        ):
            raise PermissionDenied('You must be a board member to create tasks.')

        assignee = attrs.get('assignee')
        reviewer = attrs.get('reviewer')

        if assignee and not board.members.filter(id=assignee.id).exists():
            raise serializers.ValidationError(
                {'assignee_id': 'Assignee must be a board member.'}
            )

        if reviewer and not board.members.filter(id=reviewer.id).exists():
            raise serializers.ValidationError(
                {'reviewer_id': 'Reviewer must be a board member.'}
            )

        return attrs


class TaskUpdateSerializer(serializers.ModelSerializer):
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        source='assignee',
        required=False,
        allow_null=True,
    )

    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        source='reviewer',
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'status',
            'priority',
            'assignee_id',
            'reviewer_id',
            'due_date',
        ]

    def validate(self, attrs):
        if 'board' in self.initial_data:  # type:ignore
            raise serializers.ValidationError(
                {'board': 'Changing the board is not allowed.'}
            )

        board = self.instance.board  # type:ignore

        assignee = attrs.get('assignee')
        reviewer = attrs.get('reviewer')

        if assignee and not board.members.filter(id=assignee.id).exists():
            raise serializers.ValidationError(
                {'assignee_id': 'Assignee must be a board member.'}
            )

        if reviewer and not board.members.filter(id=reviewer.id).exists():
            raise serializers.ValidationError(
                {'reviewer_id': 'Reviewer must be a board member.'}
            )

        return attrs
