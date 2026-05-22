"""
Module to simulate the process of photosynthesis and generate a report.
It calculates the rate of photosynthesis based on factors such as light intensity, temperature, CO2 concentration, and water availability.
"""

import numpy as np
import pandas as pd

class Photosynthesis:
    def __init__(self, light_intensity, temperature, co2_concentration, water_availability):
        """
        Initialize the photosynthesis process with given factors.
        
        Parameters:
        light_intensity (float): Light intensity in umol/m^2s
        temperature (float): Temperature in degree Celsius
        co2_concentration (float): CO2 concentration in ppm
        water_availability (float): Water availability in percentage
        """
        self.light_intensity = light_intensity
        self.temperature = temperature
        self.co2_concentration = co2_concentration
        self.water_availability = water_availability

    def calculate_photosynthesis_rate(self):
        """
        Calculate the rate of photosynthesis based on the given factors.
        
        Returns:
        float: Rate of photosynthesis in umol/m^2s
        """
        # Assuming a simple linear relationship between factors and photosynthesis rate
        rate = (self.light_intensity * 0.5) + (self.temperature * 0.2) + (self.co2_concentration * 0.1) + (self.water_availability * 0.2)
        return rate

    def generate_report(self):
        """
        Generate a report based on the calculated photosynthesis rate.
        
        Returns:
        dict: Report containing the calculated photosynthesis rate and other factors
        """
        rate = self.calculate_photosynthesis_rate()
        report = {
            "Photosynthesis Rate": rate,
            "Light Intensity": self.light_intensity,
            "Temperature": self.temperature,
            "CO2 Concentration": self.co2_concentration,
            "Water Availability": self.water_availability
        }
        return report

if __name__ == "__main__":
    # Create a photosynthesis object with sample factors
    photosynthesis = Photosynthesis(light_intensity=100, temperature=25, co2_concentration=400, water_availability=80)
    
    # Generate a report
    report = photosynthesis.generate_report()
    
    # Print the report
    print("Photosynthesis Report:")
    for key, value in report.items():
        print(f"{key}: {value}")