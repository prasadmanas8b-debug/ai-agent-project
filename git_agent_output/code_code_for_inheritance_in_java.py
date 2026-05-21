"""
This module demonstrates the concept of inheritance in Python, 
similar to the concept in Java. It includes examples of single 
inheritance, multilevel inheritance, and hierarchical inheritance.
"""

class Animal:
    def __init__(self, name):
        # Initialize the name attribute
        self.name = name

    def eat(self):
        # Print a message indicating the animal is eating
        print(f"{self.name} is eating")

    def sleep(self):
        # Print a message indicating the animal is sleeping
        print(f"{self.name} is sleeping")


class Dog(Animal):
    def __init__(self, name):
        # Call the parent class constructor using super()
        super().__init__(name)

    def bark(self):
        # Print a message indicating the dog is barking
        print("Dog is barking")


class Mammal(Animal):
    def __init__(self, name):
        # Call the parent class constructor using super()
        super().__init__(name)

    def walk(self):
        # Print a message indicating the mammal is walking
        print(f"{self.name} is walking")


class DogMammal(Mammal):
    def __init__(self, name):
        # Call the parent class constructor using super()
        super().__init__(name)

    def bark(self):
        # Print a message indicating the dog is barking
        print("Dog is barking")


if __name__ == "__main__":
    # Create an instance of the Dog class
    dog = Dog("Buddy")
    dog.eat()  # Output: Buddy is eating
    dog.sleep()  # Output: Buddy is sleeping
    dog.bark()  # Output: Dog is barking

    # Create an instance of the Mammal class
    mammal = Mammal("Mammal")
    mammal.eat()  # Output: Mammal is eating
    mammal.sleep()  # Output: Mammal is sleeping
    mammal.walk()  # Output: Mammal is walking

    # Create an instance of the DogMammal class
    dog_mammal = DogMammal("DogMammal")
    dog_mammal.eat()  # Output: DogMammal is eating
    dog_mammal.sleep()  # Output: DogMammal is sleeping
    dog_mammal.walk()  # Output: DogMammal is walking
    dog_mammal.bark()  # Output: Dog is barking