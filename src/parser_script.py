from selenium import webdriver
import pandas as pd
from realtylink_parser import get_links, get_data

def __main__():
    print("Welcome to the test parser script! Press Ctrl + C to stop the process.\n")
    # Set the URL of the page
    url = "https://realtylink.org/en/properties~for-rent"

    # Set up the Chrome WebDriver
    driver = webdriver.Chrome()
    # Maximize the window to achieve full-screen mode
    driver.maximize_window()
    # Navigate to the initial page
    driver.get(url)
    # Get realty links
    driver, links = get_links(driver, 60)
    # Get realty data
    driver, data = get_data(driver, links)
    # Close driver
    driver.close()
    
    df = pd.DataFrame(data)
    df.to_json("templates/realty.json")

if __name__ == "__main__":
    try:
        __main__()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Press enter to close the window...")
        input()
