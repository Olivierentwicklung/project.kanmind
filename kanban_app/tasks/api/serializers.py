from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from auth_app.models import UserProfile
from kanban_app.tasks.models import Comment, Task


class TaskUserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for task-related user information.
    """

    email = serializers.EmailField(source='user.email')

    class Meta:
        """return values of the TaskUserProfileSerializer"""

        model = UserProfile
        fields = [
            'id',
            'email',
            'fullname',
        ]


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for task overview and detail responses.
    """

    assignee = TaskUserProfileSerializer(read_only=True)
    reviewer = TaskUserProfileSerializer(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        """return values of the TaskSerializer"""

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
    """
    Serializer for task creation.
    """

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
        """return values of the TaskCreateSerializer"""

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
        """
        Validate that:
        - Only board members or owners can create tasks
        - Assigned users must belong to the same board
        - reviewer users must belong to the same board
        """

        request = self.context['request']
        user_profile = request.user.userprofile
        board = attrs.get('board')

        if board is None:
            return attrs

        # Only board members or owners can create tasks
        if not (
            board.owner == user_profile
            or board.members.filter(id=user_profile.id).exists()
        ):
            raise PermissionDenied('You must be a board member to create tasks.')

        assignee = attrs.get('assignee')
        reviewer = attrs.get('reviewer')

        # Assigned users must belong to the same board
        if assignee and not board.members.filter(id=assignee.id).exists():
            raise serializers.ValidationError(
                {'assignee_id': 'Assignee must be a board member.'}
            )

        # reviewer users must belong to the same board
        if reviewer and not board.members.filter(id=reviewer.id).exists():
            raise serializers.ValidationError(
                {'reviewer_id': 'Reviewer must be a board member.'}
            )

        return attrs

    def create(self, validated_data):
        """Create a Task"""

        # Automatically assign the authenticated user as task author
        user_profile = self.context['request'].user.userprofile

        return Task.objects.create(
            author=user_profile,
            **validated_data,
        )


class TaskUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing tasks.
    """

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
        """return values of the TaskUpdateSerializer"""

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
        """
        Validate that:
        - Prevent tasks from being moved to another board
        - Assigned users must belong to the same board
        - reviewer users must belong to the same board
        """

        # Prevent tasks from being moved to another board
        if 'board' in self.initial_data:  # type: ignore
            raise serializers.ValidationError(
                {'board': 'Changing the board is not allowed.'}
            )

        board = self.instance.board  # type: ignore

        assignee = attrs.get('assignee')
        reviewer = attrs.get('reviewer')

        # Assigned users must belong to the same board
        if assignee and not board.members.filter(id=assignee.id).exists():
            raise serializers.ValidationError(
                {'assignee_id': 'Assignee must be a board member.'}
            )

        # reviewer users must belong to the same board
        if reviewer and not board.members.filter(id=reviewer.id).exists():
            raise serializers.ValidationError(
                {'reviewer_id': 'Reviewer must be a board member.'}
            )

        return attrs


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for task comments.
    """

    author = serializers.CharField(
        source='author.fullname',
        read_only=True,
    )

    class Meta:
        """return values of the CommentSerializer"""

        model = Comment
        fields = [
            'id',
            'created_at',
            'author',
            'content',
        ]


class CommentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating task comments.
    """

    class Meta:
        """return values of the CommentCreateSerializer"""

        model = Comment
        fields = [
            'content',
        ]

    def create(self, validated_data):
        """Create a Task Comment"""

        task = self.context['task']
        author = self.context['request'].user.userprofile

        return Comment.objects.create(
            task=task,
            author=author,
            **validated_data,
        )
