# Car Damage Detection Project

This repository is part of a larger project aimed at evaluating damage on cars. Currently, this repository includes the following components:

## 1. Image Scraping
The image scraping component retrieves images from three websites: AutoMotos, SalvageReseller, and Schadeautos. The scrapers are located in the `ImageCarsScrapping` directory.

### Websites Scraped:
- **AutoMotos**: A website with a variety of car images.
- **SalvageReseller**: A site specializing in images of cars that are for sale as salvage.
- **Schadeautos**: A site with images of damaged cars.

## 2. Scripts for Image Annotation

- **Gemini API Annotation Script**: This script performs image annotation using the Gemini API and OpenAI. It fetches images from an S3 bucket, processes them using a generative model, and saves the results to a CSV file.

- **OpenAI API Annotation Script**: This script performs image annotation using the OpenAI API. It fetches images from an S3 bucket, processes them using a GPT-4 model to identify car parts and their conditions, and saves the results to a CSV file.


## 3. Cleaning Application
The cleaning application, located in the `cleaningApp` directory, is built with Flask (for the backend) and JavaScript, HTML, and CSS (for the frontend). This application allows users to annotate images. 


### Key Features:
- **Predefined Annotations**: The application uses predefined annotations generated based on Gemini & GPT.
- **User Validation**: Users can validate or correct the annotations provided by LLMs.

## Directory Structure
- `ImageCarsScrapping/`: Contains scripts for scraping images from the specified websites.
- `cleaningApp/`: Contains the Flask application for annotating images.

## Future Perspectives

After completing the annotation of damage regions in the car images, the next steps for the project include:

### Developing a Model for Damage Prediction
- Design and implement a machine learning model to predict the location and extent of damage on cars based on the annotated data.

### Segmenting Damage Regions
- Create a segmentation model to accurately delineate damaged areas on the car images, which will help in providing more detailed damage assessments.

## Getting Started

### Prerequisites
- Python 3.x
- Flask
- Datrie
- boto3
- JavaScript, HTML, and CSS for the frontend
- Necessary Python libraries listed in `requirements.txt`

### Installation

1. **Clone the repository**:
   ```sh
   git clone git@github.com:RChoukri03/CarDamageDetection-.git
   cd CarDamageDetection
