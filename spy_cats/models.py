from django.db import models
from django.core.exceptions import ValidationError

class Breed(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class SpyCat(models.Model):
    name = models.CharField(max_length=100)
    years_of_experience = models.PositiveIntegerField()
    breed = models.ForeignKey(Breed, on_delete=models.CASCADE)
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Mission(models.Model):
    cat = models.ForeignKey(SpyCat, on_delete=models.SET_NULL, null=True, blank=True)
    is_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"Mission {self.id} assigned to {self.cat.name if self.cat else 'Unassigned'}"

    def check_completion(self):
        if not self.targets.filter(is_complete=False).exists():
            self.is_complete = True
            self.save()

    def can_delete(self):
        return self.cat is None


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Target(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name='targets')
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    is_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"Target {self.name} in {self.country.name} for Mission {self.mission.id}"