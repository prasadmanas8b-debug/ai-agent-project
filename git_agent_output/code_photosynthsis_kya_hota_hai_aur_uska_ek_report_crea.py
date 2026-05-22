"""
This module simulates the process of photosynthesis and generates a report.
It calculates the rate of photosynthesis based on factors such as light intensity, temperature, CO2 concentration, and water availability.
"""

import numpy as np

class Photosynthesis:
    def __init__(self, light_intensity, temperature, co2_concentration, water_availability):
        """
        Initialize the photosynthesis process with given factors.
        
        Parameters:
        light_intensity (float): The intensity of light in μmol/m²s.
        temperature (float): The temperature in °C.
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
        float: The rate of photosynthesis in μmol/m²s.
        """
        # Assuming a simple linear relationship between factors and photosynthesis rate
        rate = (self.light_intensity * 0.1) + (self.temperature * 0.05) + (self.co2_concentration * 0.01) + (self.water_availability * 0.1)
        return rate

    def generate_report(self):
        """
        Generate a report based on the calculated photosynthesis rate.
        
        Returns:
        str: A report containing the calculated photosynthesis rate and factors.
        """
        rate = self.calculate_photosynthesis_rate()
        report = f"Photosynthesis Rate: {rate} μmol/m²s\n"
        report += f"Light Intensity: {self.light_intensity} μmol/m²s\n"
        report += f"Temperature: {self.temperature} °C\n"
        report += f"CO2 Concentration: {self.co2_concentration} ppm\n"
        report += f"Water Availability: {self.water_availability}%"
        return report

if __name__ == "__main__":
    # Create a Photosynthesis object with sample factors
    photosynthesis = Photosynthesis(light_intensity=500, temperature=25, co2_concentration=400, water_availability=80)
    
    # Generate and print the report
    report = photosynthesis.generate_report()
    print(report)