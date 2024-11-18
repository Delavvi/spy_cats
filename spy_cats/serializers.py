from rest_framework import serializers
from .models import SpyCat, Breed, Mission, Target, Country

class BreedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Breed
        fields = ('id', 'name')


class SpyCatSerializer(serializers.ModelSerializer):
    breed_name = serializers.CharField(write_only=True)
    breed = BreedSerializer(read_only=True)

    class Meta:
        model = SpyCat
        fields = ('id', 'name', 'years_of_experience', 'salary', 'breed_name', 'breed')

    def create(self, validated_data):
        breed_name = validated_data.pop('breed_name', None)
        breed = self.context['breed']
        validated_data['breed'] = breed
        return super().create(validated_data)

    def update(self, instance, validated_data):
        breed_name = validated_data.pop('breed_name', None)
        if breed_name:
            breed = self.context['breed']
            validated_data['breed'] = breed
        return super().update(instance, validated_data)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'name')


class TargetSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)

    class Meta:
        model = Target
        fields = ('id', 'name', 'country', 'notes', 'is_complete')


class MissionSerializer(serializers.ModelSerializer):
    targets = TargetSerializer(many=True)
    cat = serializers.PrimaryKeyRelatedField(queryset=SpyCat.objects.all(), allow_null=True)

    class Meta:
        model = Mission
        fields = ('id', 'cat', 'is_complete', 'targets')
