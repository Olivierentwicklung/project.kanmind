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


class BoardMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for showing a board member inside a board detail response.
    """

    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'email',
            'fullname',
        ]


class BoardTaskSummarySerializer(serializers.ModelSerializer):
    """
    Serializer for showing a short task overview inside a board detail response.
    """

    assignee = BoardMemberSerializer(read_only=True)
    reviewer = BoardMemberSerializer(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
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
    Serializer for retrieving detailed information about one board.
    """

    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    members = BoardMemberSerializer(many=True, read_only=True)
    tasks = BoardTaskSummarySerializer(many=True, read_only=True)

    class Meta:
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
    Serializer for updating an existing board.
    """

    members = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        many=True,
        required=False,
        allow_empty=False,
    )

    owner_data = BoardMemberSerializer(
        source='owner',
        read_only=True,
    )

    members_data = BoardMemberSerializer(
        source='members',
        many=True,
        read_only=True,
    )

    class Meta:
        """Configuration for BoardUpdateSerializer."""

        model = Board
        fields = [
            'id',
            'title',
            'members',
            'owner_data',
            'members_data',
        ]
