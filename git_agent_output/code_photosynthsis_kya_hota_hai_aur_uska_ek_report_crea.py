"""
This module simulates the process of photosynthesis and calculates the rate of photosynthesis based on various factors.
It provides a basic understanding of the photosynthetic process and its importance in life on Earth.
"""

import numpy as np

class Photosynthesis:
    def __init__(self, light_intensity, temperature, co2_concentration, water_availability):
        """
        Initialize the photosynthesis process with given factors.
        
        Parameters:
        light_intensity (float): The intensity of light in umol/m^2/s.
        temperature (float): The temperature in degrees Celsius.
        co2_concentration (float): The concentration of CO2 in ppm.
        water_availability (float): The availability of water in percentage.
        """
        self.light_intensity = light_intensity
        self.temperature = temperature
        self.co2_concentration = co2_concentration
        self.water_availability = water_availability

    def calculate_photosynthesis_rate(self):
        """
        Calculate the rate of photosynthesis based on the given factors.
        
        Returns:
        float: The rate of photosynthesis in umol/m^2/s.
        """
        # Assuming a simple linear relationship between factors and photosynthesis rate
        rate = (self.light_intensity * 0.5) + (self.temperature * 0.2) + (self.co2_concentration * 0.1) + (self.water_availability * 0.2)
        return rate

    def print_report(self):
        """
        Print a report on the photosynthesis process.
        """
        print("Photosynthesis Report:")
        print(f"Light Intensity: {self.light_intensity} umol/m^2/s")
        print(f"Temperature: {self.temperature} degrees Celsius")
        print(f"CO2 Concentration: {self.co2_concentration} ppm")
        print(f"Water Availability: {self.water_availability}%")
        print(f"Photosynthesis Rate: {self.calculate_photosynthesis_rate()} umol/m^2/s")

if __name__ == "__main__":
    # Create a photosynthesis object with sample values
    photosynthesis = Photosynthesis(light_intensity=100, temperature=25, co2_concentration=400, water_availability=80)
    
    # Print the report
    photosynthesis.print_report()