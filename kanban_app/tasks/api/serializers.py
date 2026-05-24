from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied

from auth_app.models import UserProfile
from kanban_app.boards.models import Board
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

    comments_count = serializers.IntegerField(read_only=True, default=0)

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
            'comments_count',
        ]

    def to_internal_value(self, data):
        """
        Runs BEFORE field validation. Intercepts raw input to force
        a 404 response if the referenced board ID is missing.
        """
        board_id = data.get('board')
        if board_id is not None:
            # Check the database before PrimaryKeyRelatedField throws a 400
            if not Board.objects.filter(id=board_id).exists():
                raise NotFound({'board': 'Board not found.'})  # Forces 404 response

        return super().to_internal_value(data)

    def validate(self, attrs):
        """Validate board permissions and user memberships in 1 query."""
        board = attrs.get('board')
        if not board:
            return attrs

        request = self.context['request']
        user_profile = request.user.userprofile

        # Fetch the board and prefetch members to optimize performance
        # (The board is guaranteed to exist now because to_internal_value passed)
        board_instance = Board.objects.prefetch_related('members').get(id=board.id)

        # Cache valid user IDs in memory for fast O(1) lookups
        valid_user_ids = set(board_instance.members.values_list('id', flat=True))

        # Use getattr to fetch owner_id safely without a Pylance warning
        owner_id = getattr(board_instance, 'owner_id', None)
        if owner_id:
            valid_user_ids.add(owner_id)

        # SECURITY CHECK: Verify user permissions
        if user_profile.id not in valid_user_ids:
            raise PermissionDenied(
                'You must be a board member to create tasks.'
            )  # Forces 403 response

        # DATA VALIDATION: Verify assignee and reviewer (returns default 400)
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

        return attrs

    def create(self, validated_data):
        """Create a Task with the current user context as the author."""

        user_profile = self.context['request'].user.userprofile
        validated_data['author'] = user_profile
        return super().create(validated_data)

    def to_representation(self, instance):
        """Dynamically morph keys to match the nested JSON response format."""

        # 1. Get standard serialized dictionary data
        representation = super().to_representation(instance)

        # 2. Swap out flat _id fields for nested detailed object structures
        representation['assignee'] = (
            TaskUserProfileSerializer(instance.assignee).data
            if instance.assignee
            else None
        )

        representation['reviewer'] = (
            TaskUserProfileSerializer(instance.reviewer).data
            if instance.reviewer
            else None
        )

        # 3. Clean up the flat keys so they don't pollute the final output
        representation.pop('assignee_id', None)
        representation.pop('reviewer_id', None)

        return representation


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
