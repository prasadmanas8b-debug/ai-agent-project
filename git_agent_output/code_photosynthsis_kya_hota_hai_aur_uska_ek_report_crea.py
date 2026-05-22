"""
Module to simulate the process of photosynthesis and generate a report.
It calculates the rate of photosynthesis based on factors such as light intensity, temperature, CO2 concentration, and water availability.
"""

import numpy as np

class Photosynthesis:
    def __init__(self, light_intensity, temperature, co2_concentration, water_availability):
        """
        Initialize the Photosynthesis class with factors affecting photosynthesis.
        
        Args:
            light_intensity (float): Light intensity in umol/m^2/s
            temperature (float): Temperature in degrees Celsius
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
            float: Rate of photosynthesis in umol/m^2/s
        """
        # Assuming a simple linear relationship between factors and photosynthesis rate
        rate = (self.light_intensity * 0.5) + (self.temperature * 0.2) + (self.co2_concentration * 0.1) + (self.water_availability * 0.2)
        return rate

    def generate_report(self):
        """
        Generate a report on the photosynthesis process.
        
        Returns:
            str: Report on photosynthesis
        """
        report = "Photosynthesis Report:\n"
        report += f"Light Intensity: {self.light_intensity} umol/m^2/s\n"
        report += f"Temperature: {self.temperature} degrees Celsius\n"
        report += f"CO2 Concentration: {self.co2_concentration} ppm\n"
        report += f"Water Availability: {self.water_availability}%\n"
        report += f"Rate of Photosynthesis: {self.calculate_photosynthesis_rate()} umol/m^2/s\n"
        return report

if __name__ == "__main__":
    # Create an instance of the Photosynthesis class
    photosynthesis = Photosynthesis(light_intensity=100, temperature=25, co2_concentration=400, water_availability=80)
    
    # Generate and print the report
    report = photosynthesis.generate_report()
    print(report)