from rest_framework import serializers

from .models import (
    Exercise,
    ExerciseSet,
    SessionExercise,
    WorkoutPlan,
    WorkoutPlanExercise,
    WorkoutSession,
)


class ExerciseSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseSet
        fields = ["id", "session_exercise", "set_number", "reps", "weight", "created_at"]
        read_only_fields = ["id", "created_at"]


class NestedExerciseSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseSet
        fields = ["set_number", "reps", "weight"]


class SessionExerciseSerializer(serializers.ModelSerializer):
    exercise_sets = NestedExerciseSetSerializer(many=True, required=False)

    class Meta:
        model = SessionExercise
        fields = [
            "id",
            "session",
            "exercise",
            "started_at",
            "ended_at",
            "order",
            "exercise_sets",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        sets_data = validated_data.pop("exercise_sets", [])
        instance = super().create(validated_data)
        if sets_data:
            ExerciseSet.objects.bulk_create(
                [
                    ExerciseSet(
                        session_exercise=instance,
                        set_number=item["set_number"],
                        reps=item["reps"],
                        weight=item["weight"],
                    )
                    for item in sets_data
                ]
            )
        return instance


class NestedSessionExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionExercise
        fields = ["exercise", "started_at", "ended_at", "order"]


class WorkoutSessionSerializer(serializers.ModelSerializer):
    session_exercises = NestedSessionExerciseSerializer(many=True, required=False)

    class Meta:
        model = WorkoutSession
        fields = [
            "id",
            "user",
            "workout_plan",
            "started_at",
            "ended_at",
            "session_exercises",
        ]
        read_only_fields = ["id", "user"]

    def validate_workout_plan(self, value):
        request = self.context.get("request")
        if request and value.user_id != request.user.id:
            raise serializers.ValidationError("Workout plan does not belong to current user.")
        return value

    def create(self, validated_data):
        exercises_data = validated_data.pop("session_exercises", [])
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["user"] = request.user
        session = super().create(validated_data)
        if exercises_data:
            SessionExercise.objects.bulk_create(
                [
                    SessionExercise(
                        session=session,
                        exercise=item["exercise"],
                        started_at=item["started_at"],
                        ended_at=item.get("ended_at"),
                        order=item["order"],
                    )
                    for item in exercises_data
                ]
            )
        return session


class WorkoutPlanExerciseSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source="exercise.name", read_only=True)

    class Meta:
        model = WorkoutPlanExercise
        fields = [
            "id",
            "workout_plan",
            "exercise",
            "exercise_name",
            "order",
            "target_sets",
            "target_reps",
            "rest_time_seconds",
        ]
        read_only_fields = ["id", "workout_plan", "exercise_name"]


class WorkoutPlanSerializer(serializers.ModelSerializer):
    plan_exercises = WorkoutPlanExerciseSerializer(many=True, required=False)

    class Meta:
        model = WorkoutPlan
        fields = [
            "id",
            "user",
            "name",
            "description",
            "started_at",
            "ended_at",
            "created_at",
            "updated_at",
            "plan_exercises",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def create(self, validated_data):
        exercises_data = validated_data.pop("plan_exercises", [])
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["user"] = request.user
        plan = super().create(validated_data)
        if exercises_data:
            WorkoutPlanExercise.objects.bulk_create(
                [
                    WorkoutPlanExercise(
                        workout_plan=plan,
                        exercise=item["exercise"],
                        order=item["order"],
                        target_sets=item["target_sets"],
                        target_reps=item["target_reps"],
                        rest_time_seconds=item.get("rest_time_seconds"),
                    )
                    for item in exercises_data
                ]
            )
        return plan

    def update(self, instance, validated_data):
        exercises_data = validated_data.pop("plan_exercises", None)
        instance = super().update(instance, validated_data)
        if exercises_data is not None:
            instance.plan_exercises.all().delete()
            if exercises_data:
                WorkoutPlanExercise.objects.bulk_create(
                    [
                        WorkoutPlanExercise(
                            workout_plan=instance,
                            exercise=item["exercise"],
                            order=item["order"],
                            target_sets=item["target_sets"],
                            target_reps=item["target_reps"],
                            rest_time_seconds=item.get("rest_time_seconds"),
                        )
                        for item in exercises_data
                    ]
                )
        return instance


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ["id", "name"]
        read_only_fields = ["id"]
