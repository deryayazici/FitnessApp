class PhysicalActivity:
    def __init__(self, weight):
        self.weight = weight

    def calculate_calories_burned(self):
        raise NotImplementedError("This method should be implemented by subclasses.")
