"""
This module provides a simulation of the photosynthesis process and generates a report.
It calculates the rate of photosynthesis based on factors such as light intensity, temperature, CO2 concentration, and water availability.
"""

import numpy as np
import pandas as pd

class Photosynthesis:
    def __init__(self, light_intensity, temperature, co2_concentration, water_availability):
        """
        Initialize the photosynthesis process with given factors.
        
        Parameters:
        light_intensity (float): Light intensity in μmol/m²s
        temperature (float): Temperature in °C
        co2_concentration (float): CO2 concentration in ppm
        water_availability (float): Water availability in mm
        """
        self.light_intensity = light_intensity
        self.temperature = temperature
        self.co2_concentration = co2_concentration
        self.water_availability = water_availability

    def calculate_photosynthesis_rate(self):
        """
        Calculate the rate of photosynthesis based on the given factors.
        
        Returns:
        float: Rate of photosynthesis in μmol/m²s
        """
        # Assuming a simple linear relationship between factors and photosynthesis rate
        rate = (self.light_intensity * 0.1) + (self.temperature * 0.05) + (self.co2_concentration * 0.01) + (self.water_availability * 0.005)
        return rate

    def generate_report(self):
        """
        Generate a report of the photosynthesis process.
        
        Returns:
        dict: Report containing the factors and calculated rate of photosynthesis
        """
        report = {
            "Light Intensity": self.light_intensity,
            "Temperature": self.temperature,
            "CO2 Concentration": self.co2_concentration,
            "Water Availability": self.water_availability,
            "Rate of Photosynthesis": self.calculate_photosynthesis_rate()
        }
        return report

if __name__ == "__main__":
    # Create a photosynthesis object with sample factors
    photosynthesis = Photosynthesis(light_intensity=500, temperature=25, co2_concentration=400, water_availability=100)
    
    # Generate and print the report
    report = photosynthesis.generate_report()
    print("Photosynthesis Report:")
    for key, value in report.items():
        print(f"{key}: {value}")