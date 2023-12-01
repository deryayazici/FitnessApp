from activities import PhysicalActivity

class Cycling(PhysicalActivity):
    def __init__(self, distance, weight):
        super().__init__(weight) 
        self.distance = distance  

    def calculate_calories_burned(self):
        distance_km = int(self.distance * 1.60934)
        weight_kg = int(self.weight * 0.453592)

        average_speed_kmh = 15
        calories_burned_per_hour_per_kg = 8.5
        total_hours = distance_km / average_speed_kmh

        total_calories_burned = int(calories_burned_per_hour_per_kg )* weight_kg * total_hours

        return int(total_calories_burned)