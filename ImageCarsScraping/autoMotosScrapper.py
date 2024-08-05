import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from bs4 import BeautifulSoup
from tqdm import tqdm
def setupWebdriver():
    options = ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver

def scrapeCarLinks(driver, url):
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return [a['href'] for a in soup.find_all('a', class_='car')]

def scrapeImageLinks(driver, link, imageCount=10):
    driver.get(link)
    imagesCollected = 0

    while imagesCollected < imageCount:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        picturesDiv = soup.find("div", class_="pictures")
        
        if not picturesDiv or not picturesDiv.find('img'):
            print(f"No more images found on {link}")
            break
        
        imgSrc = picturesDiv.img.get("src")
        yield imgSrc

        nextButtons = driver.find_elements(By.XPATH, '//div[contains(@class, "next")]')
        if nextButtons:
            driver.execute_script("arguments[0].click();", nextButtons[0])
        else:
            break
        
        imagesCollected += 1

def saveLinksToFile(imageLinks, filename="image_urls.txt"):
    with open(filename, 'a') as file:
        for link in imageLinks:
            file.write(link + '\n')

def main():
    baseUrl = "https://www.autos-motos.net"
    targetUrl = f"{baseUrl}/en/search/all?page="
    contUrl = "&sort=1"
    
    driver = setupWebdriver()
    
    try:
        for i in tqdm(range(1, 53), desc='Scrapping pages'):  
            fullUrl = f"{targetUrl}{i}{contUrl}"
            carLinks = scrapeCarLinks(driver, fullUrl)
            for link in carLinks:
                fullLink = baseUrl + link
                imageLinks = scrapeImageLinks(driver, fullLink)
                saveLinksToFile(imageLinks)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
