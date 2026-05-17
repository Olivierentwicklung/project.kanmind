from rest_framework import serializers

from auth_app.models import UserProfile
from kanban_app.boards.models import Board
from kanban_app.tasks.models import Task


class BoardListSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        many=True,
        # DRF automatically excludes write_only=True fields from the response.
        write_only=True,
        allow_empty=False,
    )

    member_count = serializers.IntegerField(read_only=True)
    ticket_count = serializers.IntegerField(read_only=True)
    tasks_to_do_count = serializers.IntegerField(read_only=True)
    tasks_high_prio_count = serializers.IntegerField(read_only=True)
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)

    class Meta:
        model = Board
        fields = [
            'id',
            'title',
            'members',
            'member_count',
            'ticket_count',
            'tasks_to_do_count',
            'tasks_high_prio_count',
            'owner_id',
        ]

    def create(self, validated_data):
        # Extract ManyToMany relation before board creation
        members = validated_data.pop('members')
        # Authenticated user becomes board owner
        owner = self.context['request'].user.userprofile

        board = Board.objects.create(
            owner=owner,
            **validated_data,
        )
        # Assign board members after board instance exists
        board.members.set(members)

        return board


class BoardUserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'email',
            'fullname',
        ]


class BoardTaskSerializer(serializers.ModelSerializer):
    assignee = BoardUserProfileSerializer(read_only=True)
    reviewer = BoardUserProfileSerializer(read_only=True)
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
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    members = BoardUserProfileSerializer(many=True, read_only=True)
    tasks = BoardTaskSerializer(many=True, read_only=True)

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
        model = Board
        fields = [
            'id',
            'title',
            'members',
            'owner_data',
            'members_data',
        ]

    def update(self, instance, validated_data):
        members = validated_data.pop('members', None)

        instance.title = validated_data.get(
            'title',
            instance.title,
        )
        instance.save()

        if members is not None:
            instance.members.set(members)

        return instance
