from activities import PhysicalActivity

class Running(PhysicalActivity):
    def __init__(self, distance, weight):
        super().__init__(weight) 
        self.distance = distance  

    def calculate_calories_burned(self):
        distance_km = self.distance * 1.60934
        weight_kg = self.weight * 0.453592
        calories_burned_per_km = 0.75 * weight_kg
        return int(calories_burned_per_km * distance_km)

