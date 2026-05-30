from rest_framework import serializers

from auth_app.models import UserProfile
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


class TaskCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a task.

     This serializer is responsible for:
    - receiving task creation data from the API request
    - validating assignee and reviewer users
    - making sure assignee/reviewer belong to the board
    - automatically setting the task author
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
    comments_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        """Configure fields for task creation."""

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
        """Validate the incoming task data before creating the task."""

        board = self.context.get('board') or attrs.get('board')

        if not board:
            return attrs

        assignee = attrs.get('assignee')
        reviewer = attrs.get('reviewer')

        valid_user_ids = set(board.members.values_list('id', flat=True))

        if board.owner:
            valid_user_ids.add(board.owner.id)

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
        """
        Create the task and automatically set the authenticated user as author.
        """

        user_profile = getattr(self.context['request'].user, 'userprofile', None)
        validated_data['author'] = user_profile

        return super().create(validated_data)


class TaskUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing tasks.
    """

    # Links an optional UserProfile ID to the 'assignee' model relation
    # and allows null values.
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        source='assignee',
        required=False,
        allow_null=True,
    )

    # Links an optional UserProfile ID to the 'reviewer' model relation
    # and allows null values.
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        source='reviewer',
        required=False,
        allow_null=True,
    )

    # Computed read-only field mapping to a property/annotation on your model
    comments_count = serializers.IntegerField(read_only=True, default=0)

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
            'comments_count',
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

    def to_representation(self, instance):
        """Dynamically morph keys to match the nested JSON response format."""

        # 1. Get standard serialized dictionary data
        representation = super().to_representation(instance)

        # 2. Swap out flat _id fields for nested detailed object structures
        representation['assignee'] = (
            TaskUserSerializer(instance.assignee).data if instance.assignee else None
        )

        representation['reviewer'] = (
            TaskUserSerializer(instance.reviewer).data if instance.reviewer else None
        )

        # 3. Clean up the flat keys so they don't pollute the final output
        representation.pop('assignee_id', None)
        representation.pop('reviewer_id', None)

        return representation


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
    """Serializer used for handling comment validation and creation."""

    class Meta:
        model = Comment
        fields = ['id', 'content']  # Ensure 'id' is present in fields array

    def create(self, validated_data):
        """Create a Task Comment using context injections."""
        task = self.context['task']
        author = getattr(self.context['request'].user, 'userprofile', None)

        validated_data['task'] = task
        validated_data['author'] = author

        return super().create(validated_data)

    def to_representation(self, instance):  # type:ignore
        """Morph output data to use the complete read serializer format."""

        return CommentSerializer(instance, context=self.context).data
