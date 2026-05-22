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
        light_intensity (float): The intensity of light in umol/m^2s
        temperature (float): The temperature in degrees Celsius
        co2_concentration (float): The concentration of CO2 in ppm
        water_availability (float): The availability of water in percentage
        """
        self.light_intensity = light_intensity
        self.temperature = temperature
        self.co2_concentration = co2_concentration
        self.water_availability = water_availability

    def calculate_rate(self):
        """
        Calculate the rate of photosynthesis based on the given factors.
        
        Returns:
        float: The rate of photosynthesis in umol/m^2s
        """
        # Assuming a simple linear relationship between factors and rate of photosynthesis
        rate = (self.light_intensity * 0.1) + (self.temperature * 0.05) + (self.co2_concentration * 0.01) + (self.water_availability * 0.1)
        return rate

    def print_report(self):
        """
        Print a report on the photosynthetic process and its factors.
        """
        print("Photosynthesis Report:")
        print(f"Light Intensity: {self.light_intensity} umol/m^2s")
        print(f"Temperature: {self.temperature} degrees Celsius")
        print(f"CO2 Concentration: {self.co2_concentration} ppm")
        print(f"Water Availability: {self.water_availability}%")
        print(f"Rate of Photosynthesis: {self.calculate_rate()} umol/m^2s")

if __name__ == "__main__":
    # Create a photosynthesis object with sample factors
    photosynthesis = Photosynthesis(light_intensity=100, temperature=25, co2_concentration=400, water_availability=80)
    
    # Print the report
    photosynthesis.print_report()