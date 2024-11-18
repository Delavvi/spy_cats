from rest_framework import viewsets, status
from rest_framework.response import Response
import requests
from .models import SpyCat, Mission, Target, Breed, Country
from .serializers import SpyCatSerializer, MissionSerializer
from django.core.exceptions import ValidationError

class SpyCatViewSet(viewsets.ModelViewSet):
    queryset = SpyCat.objects.all()
    serializer_class = SpyCatSerializer

    def validate_breed_name(self, breed_name):
        response = requests.get('https://api.thecatapi.com/v1/breeds')
        if response.status_code == 200:
            breeds_data = response.json()
            breed_names = [breed['name'].lower() for breed in breeds_data]
            if breed_name.lower() in breed_names:
                breed, created = Breed.objects.get_or_create(name=breed_name)
                return breed
            else:
                raise ValidationError({'breed_name': 'Invalid breed name.'})
        else:
            raise ValidationError({'breed_name': 'Could not validate breed name at this time.'})

    def create(self, request, *args, **kwargs):
        breed_name = request.data.get('breed_name')
        if not breed_name:
            return Response({'breed_name': 'This field is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            breed = self.validate_breed_name(breed_name)
        except ValidationError as e:
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.context['breed'] = breed
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        breed_name = request.data.get('breed_name')
        if breed_name:
            try:
                breed = self.validate_breed_name(breed_name)
            except ValidationError as e:
                return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
        else:
            breed = None

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        if breed:
            serializer.context['breed'] = breed
        self.perform_update(serializer)

        return Response(serializer.data)


class MissionViewSet(viewsets.ModelViewSet):
    queryset = Mission.objects.all()
    serializer_class = MissionSerializer

    def create(self, request, *args, **kwargs):
        data_copy = request.data.copy()
        targets_data = data_copy.pop('targets', [])
        cat_id = data_copy.get('cat')

        if cat_id:
            try:
                cat = SpyCat.objects.get(id=cat_id)
            except SpyCat.DoesNotExist:
                return Response({"detail": "Cat does not exist."}, status=status.HTTP_400_BAD_REQUEST)
            if Mission.objects.filter(cat=cat, is_complete=False).exists():
                return Response({"detail": "This cat already has an assigned mission."},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            cat = None

        if not isinstance(targets_data, list):
            return Response({"detail": "Targets data must be a list of dictionaries."},
                            status=status.HTTP_400_BAD_REQUEST)

        for target_data_dict in targets_data:
            if not isinstance(target_data_dict, dict):
                return Response({"detail": "Each target must be a dictionary."}, status=status.HTTP_400_BAD_REQUEST)

        if not (1 <= len(targets_data) <= 3):
            return Response({"detail": "Mission must have between 1 and 3 targets."},
                            status=status.HTTP_400_BAD_REQUEST)

        mission = Mission.objects.create(cat=cat, is_complete=data_copy.get('is_complete', False))

        for target_data in targets_data:
            country_name = target_data.pop('country_name', None)

            if not country_name or country_name == '':
                mission.delete()
                return Response({"detail": "Each target must have a country_name."}, status=status.HTTP_400_BAD_REQUEST)

            country, created = Country.objects.get_or_create(name=country_name)
            Target.objects.create(mission=mission, country=country, **target_data)

        mission.check_completion()

        serializer = self.get_serializer(mission)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    def update(self, request, *args, **kwargs):
        mission = self.get_object()
        data = request.data.copy()
        targets_data = data.pop('targets', None)
        cat_id = data.get('cat')

        if mission.is_complete:
            return Response({"detail": "Cannot update a completed mission."}, status=status.HTTP_400_BAD_REQUEST)

        if 'cat' in data:
            if cat_id:
                try:
                    cat = SpyCat.objects.get(id=cat_id)
                except SpyCat.DoesNotExist:
                    return Response({"detail": "Cat does not exist."}, status=status.HTTP_400_BAD_REQUEST)
                if Mission.objects.filter(cat=cat, is_complete=False).exclude(id=mission.id).exists():
                    return Response({"detail": "This cat already has an assigned mission."},
                                    status=status.HTTP_400_BAD_REQUEST)
                mission.cat = cat
            else:
                mission.cat = None

        if 'is_complete' in data:
            mission.is_complete = data.get('is_complete', mission.is_complete)

        mission.save()

        if targets_data is not None:
            if not isinstance(targets_data, list):
                return Response({"detail": "Targets data must be a list of dictionaries."},
                                status=status.HTTP_400_BAD_REQUEST)

            for target_data in targets_data:
                if not isinstance(target_data, dict):
                    return Response({"detail": "Each target must be a dictionary."}, status=status.HTTP_400_BAD_REQUEST)

                target_id = target_data.get('id', None)
                if target_id:
                    try:
                        target = Target.objects.get(id=target_id, mission=mission)
                    except Target.DoesNotExist:
                        return Response({"detail": f"Target with id {target_id} does not exist in this mission."},
                                        status=status.HTTP_400_BAD_REQUEST)

                    if target.is_complete or mission.is_complete:
                        if 'notes' in target_data:
                            return Response({"detail": "Cannot update notes of a completed target or mission."},
                                            status=status.HTTP_400_BAD_REQUEST)

                    for attr, value in target_data.items():
                        setattr(target, attr, value)
                    target.save()

                    if target.is_complete:
                        mission.check_completion()

                else:
                    if mission.targets.count() >= 3:
                        return Response({"detail": "Cannot have more than 3 targets in a mission."},
                                        status=status.HTTP_400_BAD_REQUEST)
                    Target.objects.create(mission=mission, **target_data)

        serializer = self.get_serializer(mission)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        mission = self.get_object()
        if not mission.can_delete():
            return Response({'detail': 'Cannot delete a mission assigned to a cat.'}, status=status.HTTP_400_BAD_REQUEST)
        mission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)