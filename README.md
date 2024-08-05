# Car Damage Detection Project

This repository is part of a larger project aimed at evaluating damage on cars. Currently, this repository includes the following components:

## 1. Image Scraping
The image scraping component retrieves images from three websites: AutoMotos, SalvageReseller, and Schadeautos. The scrapers are located in the `ImageCarsScrapping` directory.

### Websites Scraped:
- **AutoMotos**: A website with a variety of car images.
- **SalvageReseller**: A site specializing in images of cars that are for sale as salvage.
- **Schadeautos**: A site with images of damaged cars.

## 2. Cleaning Application
The cleaning application, located in the `cleaningApp` directory, is built with Flask (for the backend) and JavaScript, HTML, and CSS (for the frontend). This application allows users to annotate images. 

### Key Features:
- **Predefined Annotations**: The application uses predefined annotations generated based on Gemini.
- **User Validation**: Users can validate or correct the annotations provided by Gemini.

## Directory Structure
- `ImageCarsScrapping/`: Contains scripts for scraping images from the specified websites.
- `cleaningApp/`: Contains the Flask application for annotating images.

## Getting Started

### Prerequisites
- Python 3.x
- Flask
- Datrie
- JavaScript, HTML, and CSS for the frontend
- Necessary Python libraries listed in `requirements.txt`

### Installation

1. **Clone the repository**:
   ```sh
   git clone git@github.com:RChoukri03/CarDamageDetection-.git
   cd CarDamageDetection
