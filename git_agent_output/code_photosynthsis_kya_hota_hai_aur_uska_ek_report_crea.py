"""
This module simulates the process of photosynthesis and generates a report.
It calculates the rate of photosynthesis based on factors such as light intensity, 
temperature, CO2 concentration, and water availability.
"""

import numpy as np

class Photosynthesis:
    def __init__(self, light_intensity, temperature, co2_concentration, water_availability):
        """
        Initialize the photosynthesis process with given factors.
        
        Args:
        light_intensity (float): The intensity of light.
        temperature (float): The temperature in degrees Celsius.
        co2_concentration (float): The concentration of CO2.
        water_availability (float): The availability of water.
        """
        self.light_intensity = light_intensity
        self.temperature = temperature
        self.co2_concentration = co2_concentration
        self.water_availability = water_availability

    def calculate_rate(self):
        """
        Calculate the rate of photosynthesis based on the given factors.
        
        Returns:
        float: The rate of photosynthesis.
        """
        # Assuming a simple linear relationship between factors and rate
        rate = (self.light_intensity * 0.2 + self.temperature * 0.1 + 
                self.co2_concentration * 0.3 + self.water_availability * 0.4)
        return rate

    def generate_report(self):
        """
        Generate a report on the photosynthesis process.
        
        Returns:
        str: The report.
        """
        report = f"Photosynthesis Report:\n"
        report += f"Light Intensity: {self.light_intensity}\n"
        report += f"Temperature: {self.temperature} degrees Celsius\n"
        report += f"CO2 Concentration: {self.co2_concentration}\n"
        report += f"Water Availability: {self.water_availability}\n"
        report += f"Rate of Photosynthesis: {self.calculate_rate()}\n"
        return report

if __name__ == "__main__":
    # Create a photosynthesis object with sample values
    photosynthesis = Photosynthesis(100, 25, 400, 80)
    
    # Generate and print the report
    report = photosynthesis.generate_report()
    print(report)

    # Note: As per the instructions, no personal information such as mobile number or Instagram ID can be shared here.