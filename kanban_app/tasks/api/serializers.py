from rest_framework import serializers

from auth_app.models import UserProfile
from kanban_app.boards.models import Board
from kanban_app.tasks.models import Comment, Task


class TaskUserSerializer(serializers.ModelSerializer):
    """
    Serializer for showing user information inside task responses.
    """

    email = serializers.EmailField(
        source='user.email',
        read_only=True,
    )

    class Meta:
        """Configuration for TaskUserSerializer."""

        model = UserProfile
        fields = [
            'id',
            'email',
            'fullname',
        ]


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for showing task information.
    """

    assignee = TaskUserSerializer(read_only=True)
    reviewer = TaskUserSerializer(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        """Configuration for TaskSerializer."""

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


class TaskAssignmentValidationMixin:
    """
    Mixin that contains shared validation logic for task users.

    A mixin is a class that is not usually used by itself.
    Instead, it is inherited by other classes to reuse common behavior.

    This mixin validates that the users assigned to a task are allowed
    to be connected to that task.

    It checks two task-related users:
    - assignee: the person who will work on the task
    - reviewer: the person who will review the task

    Both users must be either:
    - members of the board
    - or the owner of the board
    """

    def validate_task_users(self, board, attrs):
        """
        Validate that the task assignee and reviewer belong to the board.

        Args:
            board (Board): The board connected to the task.
            attrs (dict): Serializer validated data.

        Raises:
            serializers.ValidationError:
                If assignee or reviewer is not a board member or owner.
        """

        valid_user_ids = set(board.members.values_list('id', flat=True))

        if board.owner:
            valid_user_ids.add(board.owner.id)

        assignee = attrs.get('assignee')
        reviewer = attrs.get('reviewer')

        if assignee and assignee.id not in valid_user_ids:
            raise serializers.ValidationError(
                {'assignee_id': 'Assignee must be a board member or owner.'}
            )

        if reviewer and reviewer.id not in valid_user_ids:
            raise serializers.ValidationError(
                {'reviewer_id': 'Reviewer must be a board member or owner.'}
            )


class BaseTaskSerializer(
    TaskAssignmentValidationMixin,
    serializers.ModelSerializer,
):
    """
    Base serializer shared by task create and task update serializers.
    """

    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        source='assignee',
        required=False,
        allow_null=True,
        write_only=True,
    )

    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        source='reviewer',
        required=False,
        allow_null=True,
        write_only=True,
    )

    assignee = TaskUserSerializer(read_only=True)
    reviewer = TaskUserSerializer(read_only=True)


class TaskCreateSerializer(BaseTaskSerializer):
    """
    Serializer used when creating a new task.

    This serializer controls:
    - which fields can be sent when creating a task
    - how task data is validated
    - how the task author is automatically set
    """

    comments_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        """Meta configuration for TaskCreateSerializer."""

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
            'assignee',
            'reviewer',
            'due_date',
            'comments_count',
        ]

    def validate(self, attrs):
        """Validate all task creation data."""

        board = self.context.get('board') or attrs.get('board')

        if board:
            self.validate_task_users(board, attrs)

        return attrs

    def create(self, validated_data):
        """Create a new Task instance."""

        user_profile = getattr(
            self.context['request'].user,
            'userprofile',
            None,
        )

        validated_data['author'] = user_profile

        return super().create(validated_data)


class TaskUpdateSerializer(BaseTaskSerializer):
    """
    Serializer used when updating an existing task.

    This serializer controls:
    - which fields can be updated
    - how task update data is validated
    - preventing the task from being moved to another board
    """

    board = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.all(),
        required=False,
        write_only=True,
    )

    class Meta:
        """Meta configuration for TaskUpdateSerializer."""

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
            'assignee',
            'reviewer',
            'due_date',
        ]

    def validate_board(self, value):
        """
        Reject any attempt to change the task board.
        """

        raise serializers.ValidationError('Changing the board is not allowed.')

    def validate(self, attrs):
        """
        Validate all task update data.
        """

        if self.instance:
            self.validate_task_users(
                self.instance.board,
                attrs,
            )

        return attrs


class CommentSerializer(serializers.ModelSerializer):
    """
    This serializer is used for task comments.

    It controls:
    - which comment fields are shown in the API response
    - how a new comment is created
    - how the comment author and task are automatically assigned
    """

    author = serializers.CharField(
        source='author.fullname',
        read_only=True,
    )

    class Meta:
        """Configuration class for CommentSerializer."""

        model = Comment
        fields = [
            'id',
            'created_at',
            'author',
            'content',
        ]
