from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from .models import SpyCat, Mission, Target, Breed, Country

class SpyCatViewSetTests(APITestCase):
    @patch('requests.get')
    def test_create_spycat_with_valid_breed(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{'name': 'Siamese'}]

        payload = {
            "name": "Whiskers",
            "years_of_experience": 5,
            "salary": "60000.00",
            "breed_name": "Siamese"
        }
        response = self.client.post('/spycats/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Whiskers")
        self.assertEqual(response.data['breed']['name'], "Siamese")
        self.assertTrue(Breed.objects.filter(name="Siamese").exists())

    @patch('requests.get')
    def test_create_spycat_with_invalid_breed(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{'name': 'Siamese'}]

        payload = {
            "name": "Mittens",
            "years_of_experience": 3,
            "salary": "40000.00",
            "breed_name": "UnknownBreed"
        }
        response = self.client.post('/spycats/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('breed_name', response.data)

    @patch('requests.get')
    def test_update_spycat_with_new_breed(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{'name': 'Persian'}]

        breed = Breed.objects.create(name="Siamese")
        spycat = SpyCat.objects.create(name="Whiskers", years_of_experience=5, salary="60000.00", breed=breed)

        payload = {
            "breed_name": "Persian"
        }
        response = self.client.patch(f'/spycats/{spycat.id}/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['breed']['name'], "Persian")
        self.assertTrue(Breed.objects.filter(name="Persian").exists())

    @patch('requests.get')
    def test_create_spycat_when_catapi_fails(self, mock_get):
        mock_get.return_value.status_code = 500

        payload = {
            "name": "Shadow",
            "years_of_experience": 2,
            "salary": "30000.00",
            "breed_name": "Siamese"
        }
        response = self.client.post('/spycats/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('breed_name', response.data)

    def test_delete_spycat(self):
        breed = Breed.objects.create(name="Siamese")
        spycat = SpyCat.objects.create(name="Whiskers", years_of_experience=5, salary="60000.00", breed=breed)

        response = self.client.delete(f'/spycats/{spycat.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SpyCat.objects.filter(id=spycat.id).exists())

    def test_update_spycat_salary(self):
        breed = Breed.objects.create(name="Siamese")
        spycat = SpyCat.objects.create(name="Mittens", years_of_experience=3, salary="40000.00", breed=breed)

        payload = {
            "salary": "45000.00"
        }
        response = self.client.patch(f'/spycats/{spycat.id}/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['salary'], "45000.00")
        spycat.refresh_from_db()
        self.assertEqual(spycat.salary, 45000.00)

    def test_list_spycats(self):
        breed = Breed.objects.create(name="Siamese")
        SpyCat.objects.create(name="Whiskers", years_of_experience=5, salary="60000.00", breed=breed)
        SpyCat.objects.create(name="Mittens", years_of_experience=3, salary="40000.00", breed=breed)

        response = self.client.get('/spycats/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_spycat(self):
        breed = Breed.objects.create(name="Siamese")
        spycat = SpyCat.objects.create(name="Shadow", years_of_experience=2, salary="30000.00", breed=breed)

        response = self.client.get(f'/spycats/{spycat.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Shadow")
        self.assertEqual(response.data['breed']['name'], "Siamese")

class MissionViewSetTests(APITestCase):
    def setUp(self):
        breed = Breed.objects.create(name="Siamese")
        self.spycat = SpyCat.objects.create(name="Whiskers", years_of_experience=5, salary="60000.00", breed=breed)
        self.country_usa = Country.objects.create(name="USA")
        self.country_canada = Country.objects.create(name="Canada")

    def test_create_mission_with_valid_targets(self):
        payload = {
            "cat": self.spycat.id,
            "targets": [
                {"name": "Target 1", "country_name": "USA", "notes": "Important", "is_complete": False},
                {"name": "Target 2", "country_name": "Canada", "notes": "Backup plan", "is_complete": False}
            ]
        }
        response = self.client.post('/missions/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['cat'], self.spycat.id)
        self.assertEqual(len(response.data['targets']), 2)

        mission = Mission.objects.get(id=response.data['id'])
        self.assertEqual(mission.targets.count(), 2)
        target_countries = [target.country.name for target in mission.targets.all()]
        self.assertIn("USA", target_countries)
        self.assertIn("Canada", target_countries)

    def test_create_mission_with_too_many_targets(self):
        payload = {
            "cat": self.spycat.id,
            "is_complete": False,
            "targets": [
                {"name": "Target 1", "country_name": "USA", "notes": "", "is_complete": False},
                {"name": "Target 2", "country_name": "Canada", "notes": "", "is_complete": False},
                {"name": "Target 3", "country_name": "USA", "notes": "", "is_complete": False},
                {"name": "Target 4", "country_name": "Canada", "notes": "", "is_complete": False}
            ]
        }
        response = self.client.post('/missions/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_update_mission_with_completed_target(self):
        mission = Mission.objects.create(cat=self.spycat, is_complete=False)
        target = Target.objects.create(mission=mission, name="Target 1", country=self.country_usa, is_complete=False)

        payload = {
            "targets": [{"id": target.id, "is_complete": True}]
        }
        response = self.client.patch(f'/missions/{mission.id}/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Target.objects.get(id=target.id).is_complete)
        self.assertTrue(Mission.objects.get(id=mission.id).is_complete)

    def test_update_target_notes(self):
        mission = Mission.objects.create(cat=self.spycat, is_complete=False)
        target = Target.objects.create(mission=mission, name="Target 1", country=self.country_usa, notes="Old notes", is_complete=False)

        payload = {
            "targets": [{"id": target.id, "notes": "Updated notes"}]
        }
        response = self.client.patch(f'/missions/{mission.id}/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        target.refresh_from_db()
        self.assertEqual(target.notes, "Updated notes")

    def test_update_notes_on_completed_target(self):
        mission = Mission.objects.create(cat=self.spycat, is_complete=False)
        target = Target.objects.create(mission=mission, name="Target 1", country=self.country_usa, notes="Old notes", is_complete=True)

        payload = {
            "targets": [{"id": target.id, "notes": "Attempted update"}]
        }
        response = self.client.patch(f'/missions/{mission.id}/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        target.refresh_from_db()
        self.assertEqual(target.notes, "Old notes")

    def test_target_field_validation(self):
        payload = {
            "cat": self.spycat.id,
            "targets": [
                {"name": "", "country_name": "USA", "notes": "Important", "is_complete": False},
                {"name": "Target 2", "country_name": "", "notes": "Backup plan", "is_complete": False}
            ]
        }
        response = self.client.post('/missions/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual({'detail': 'Each target must have a country_name.'}, response.data)
