from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time

def get_links(driver, quant):
    """Get desired amount of realty links.

    Args:
        driver (webdriver): Selenium Chrome webdriver.
        quant (int): Number of links.

    Returns:
        driver (webdriver): Selenium Chrome webdriver.
        links (list): list containing realty links.
        
    Raises:
        TimeoutError: if revenue is zero.
    """
    links = []
    retries = 0
    prev_page = 0  #This variable helps iterate through pages 
    # Iterate through pages    
    while retries <= 3:
        for i in range(0, round(quant / 20)):
            start_time = time.monotonic()
            while True:
                pager_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'pager-current'))
                )
                current_page_text = pager_element.text
                current_page = int(current_page_text.split('/')[0].strip())
            
                if current_page - prev_page == 1:
                    # Extract data from the current page if the page have changed
                    page = driver.page_source
                    # Parse the HTML content
                    soup = BeautifulSoup(page, 'html.parser')
                    # Find all the <a> elements with class 'property-thumbnail-summary-link'
                    link_elements = soup.find_all('a', class_='property-thumbnail-summary-link')
                    # Extract the 'href' attribute from each <a> element. These are our links.
                    links.extend([link['href'] for link in link_elements])
                    prev_page = current_page
                    break

                # Check for timeout
                end_time = time.monotonic()        
                if end_time - start_time > 10:
                    raise TimeoutError("Timeout!")                

            # Find and click the "Next" button
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'li.next a'))
                )
                next_button.click()
            except Exception as e:
                # Break the loop if the "Next" button is not found
                print(f"Error: {e}")
                retries += 1
                break
        break
    return driver, links

def get_data(driver, links):
    """Get realty data from links.

    Args:
        driver (webdriver): Selenium Chrome webdriver.
        links (list): list containing realty links.

    Returns:
        driver (webdriver): Selenium Chrome webdriver.
        data (list): list containing dictionaries with realty data.
    """
    data = []
    url = "https://realtylink.org"
    for link in links:
        page_link = url + link
        driver.get(url = page_link)
        # Wait for page to load
        time.sleep(1)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'pager-current'))
        )
        # Find title
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//span[@data-id="PageTitle"]'))
        )
        title = title_element.text

        # Find adress and region
        address_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//h2[@itemprop="address" and contains(@class, "pt-1")]'))
        )
        address = address_element.text
        address_split = address.split(', ')
        region = ""
        for element in address_split[1:]:
            region += element + ", "
        region = region[:-2]

        # Find description
        try:
            description_element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH, '//div[@itemprop="description"]'))
            )
            description = description_element.text
        except:
            description = None
        
        # Find price
        price_element = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'price.text-right'))
        )
        price = price_element.text

        # Find rooms
        try:
            bedrooms_element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'cac'))
            )
            bedrooms = int(bedrooms_element.text.split(' ')[0])
        except:
            bedrooms = None
        try:
            bathrooms_element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'sdb'))
            )
            bathrooms = int(bathrooms_element.text.split(' ')[0])
        except:
            bathrooms = None        

        # Find area
        area_element = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'carac-value'))
        )
        area = int(area_element.text.split(' ')[0].replace(',', ''))
        
        #Find image urls
        image_button = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'primary-photo-container'))
        )
        image_button.click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'carousel'))
        )
        image_urls = []
        stop = False
        while not stop:
            img = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'fullImg'))
            )
            WebDriverWait(driver, 10).until(
                EC.text_to_be_present_in_element_attribute((By.ID, 'fullImg'), "src", "http")
            )
            image_urls.append(img.get_attribute("src"))
            # Create an ActionChains object
            actions = ActionChains(driver)
            # Press the right arrow key
            actions.send_keys(Keys.ARROW_RIGHT)
            # Perform the action
            actions.perform()

            img_retries = 0
            while img_retries <= 5:
                try:
                    desc_element = WebDriverWait(driver, 1).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@class="description"]/strong'))
                    )
                    desc = desc_element.text.split("/")
                    if desc[0] == desc[1]:
                        stop = True
                        img = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, 'fullImg'))
                        )
                        WebDriverWait(driver, 10).until(
                            EC.text_to_be_present_in_element_attribute((By.ID, 'fullImg'), "src", "mediaserver")
                        )
                        image_urls.append(img.get_attribute("src"))
                    break
                except:
                    img_retries += 1

        # Generate timestamp for the data
        last_check_date = pd.Timestamp(datetime.now())

        # Create page data dictionary
        page_data = {
            "page_link": page_link,
            "title": title,
            "address": address,
            "region": region,
            "description": description,
            "price": price,
            'bedrooms': bedrooms,
            "bathrooms": bathrooms,
            "area": area,
            "image_urls": image_urls,
            "last_check_date": last_check_date,
        }

        # Add data
        data.append(page_data)
        # Refresh, so any bugs wouldn't occure
        driver.refresh()

    return driver, data
