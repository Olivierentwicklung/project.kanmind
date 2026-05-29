from rest_framework import serializers

from auth_app.models import UserProfile
from kanban_app.boards.models import Board
from kanban_app.tasks.models import Task


class BoardSummarySerializer(serializers.ModelSerializer):
    """
    Serializer used to show a short summary of a Board.
    """

    member_count = serializers.IntegerField(read_only=True)
    ticket_count = serializers.IntegerField(read_only=True)
    tasks_to_do_count = serializers.IntegerField(read_only=True)
    tasks_high_prio_count = serializers.IntegerField(read_only=True)
    owner_id = serializers.IntegerField(source='owner.user.id', read_only=True)

    class Meta:
        """Configuration class for BoardSummarySerializer."""

        model = Board
        fields = [
            'id',
            'title',
            'member_count',
            'ticket_count',
            'tasks_to_do_count',
            'tasks_high_prio_count',
            'owner_id',
        ]


class BoardCreateSerializer(serializers.ModelSerializer):
    """Serializer used to create a new Board."""

    members = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.select_related('user'),
        many=True,
        required=True,
        allow_empty=False,
    )

    class Meta:
        """Configuration class for BoardCreateSerializer."""

        model = Board
        fields = [
            'title',
            'members',
        ]


class BoardUserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for board member information.
    """

    email = serializers.EmailField(source='user.email')

    class Meta:
        """return values of the BoardUserProfileSerializer"""

        model = UserProfile
        fields = [
            'id',
            'email',
            'fullname',
        ]


class BoardTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for board task overview data.
    """

    assignee = BoardUserProfileSerializer(read_only=True)
    reviewer = BoardUserProfileSerializer(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        """return values of the BoardTaskSerializer"""

        model = Task
        fields = [
            'id',
            'title',
            'description',
            'status',
            'priority',
            'assignee',
            'reviewer',
            'due_date',
            'comments_count',
        ]


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed board information.
    """

    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    members = BoardUserProfileSerializer(many=True, read_only=True)
    tasks = BoardTaskSerializer(many=True, read_only=True)

    class Meta:
        """return values of the BoardDetailSerializer"""

        model = Board
        fields = [
            'id',
            'title',
            'owner_id',
            'members',
            'tasks',
        ]


class BoardUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating board data and members.
    """

    # Allow clients to pass members IDs when creating or updating
    members = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        many=True,
        required=False,
        allow_empty=False,
    )

    owner_data = BoardUserProfileSerializer(
        source='owner',
        read_only=True,
    )

    members_data = BoardUserProfileSerializer(
        source='members',
        many=True,
        read_only=True,
    )

    class Meta:
        """return values of the BoardUpdateSerializer"""

        model = Board
        fields = [
            'id',
            'title',
            'members',
            'owner_data',
            'members_data',
        ]
