from rest_framework import serializers

from auth_app.models import UserProfile
from kanban_app.boards.models import Board


class BoardListSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        many=True,
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
            'member_count',
            'ticket_count',
            'tasks_to_do_count',
            'tasks_high_prio_count',
            'owner_id',
        ]

    def create(self, validated_data):
        members = validated_data.pop('members')
        owner = self.context['request'].user.userprofile

        board = Board.objects.create(
            owner=owner,
            **validated_data,
        )

        board.members.set(members)

        return board
