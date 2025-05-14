import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import json
import tempfile
import os

excel_file = "./data/instamart_product_up.xlsx"
with open('data.json', 'r') as file:
    data = json.load(file)

def location_entry(pincode, driver):
    try:
        driver.get("https://www.swiggy.com/")
        WebDriverWait(driver, 10)
        location = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "location")))
        location.send_keys(pincode)
        location.send_keys(Keys.RETURN)
        location_result = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((
            By.XPATH,
            f"//div[@role='button']//span[contains(text(), '{pincode}')]"
        )))
        location_result.click()
        time.sleep(10)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(15)
        driver.quit()
        exit()

def data_scraper(pincode, product_url, driver):
    try:
        try:
            driver.get(product_url)
            time.sleep(5)
            WebDriverWait(driver, 10)
            product_name = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1"))).text
            print("Product Name:", product_name)
            seller_info = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "_8jgsH")))
            seller_info_lines = seller_info.find_elements(By.TAG_NAME, "p")
            seller_details = [line.text for line in seller_info_lines]
            store_address = " ".join(seller_details)
            print("Store Adress:", store_address)
            final_price = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@data-testid='item-offer-price']"))).text
            mrp_price = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@data-testid='item-mrp-price']"))).text
            print("Final Price:", final_price)
            print("MRP:", mrp_price)
            json_ld_script = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//script[@type='application/ld+json']"))
            )
            json_data = json.loads(json_ld_script.get_attribute("innerHTML"))
            brand_name = json_data['brand']['name']
            print("Brand Name:", brand_name)
            var = []
            buttons = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//button[@data-testid="add_buttons_center"]')))
            if buttons:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", buttons[0])
                    driver.execute_script("arguments[0].click();", buttons[0])
                    print("First button clicked.")
                except Exception as e:
                    print("Click failed:", e)
            else:
                print("No buttons found.")
            time.sleep(5)
            try:
                variants = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//div[@data-testid="variants-container"]')))
                for variant in variants:
                    try:
                        names = variant.find_elements(By.XPATH, './/div[@data-testid="variants-name"]')
                        variant_name = ' '.join([n.text for n in names])
                        price = variant.find_element(By.XPATH, './/div[@data-testid="item-offer-price"]').text
                        mrp = variant.find_element(By.XPATH, './/div[@data-testid="item-mrp-price"]').text
                        try:
                            discount = variant.find_element(By.XPATH, './/div[@data-testid="item-offer-label-discount-text"]').text
                        except:
                            discount = 'No discount'
                        try:
                            sold_out = variant.find_element(By.XPATH, './/div[@data-testid="sold-out"]').text
                        except:
                            sold_out = 'In stock'
                        print({
                            'variant': variant_name,
                            'price': price,
                            'mrp': mrp,
                            'discount': discount,
                            'status': sold_out
                        })
                        var.append({
                            'Variant Size': variant_name,
                            'Price': price,
                            'MRP': mrp,
                            'Discount': discount,
                            'Status': sold_out
                        })
                    except Exception as e:
                        print("Error extracting a variant:", e)
            except Exception as e:
                var.append('No variants')
            data = {
                "Product_Name": product_name,
                "Brand": brand_name,
                "MRP_Price": mrp_price,
                "Final_Selling_Price": final_price,
                "Store_Address": store_address,
                "Variants": [var],
                "Product_URL": product_url,
                "Input_Pincode": pincode
            }
            if os.path.exists(excel_file):
                existing_df = pd.read_excel(excel_file)
                new_df = pd.DataFrame([data])
                final_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                final_df = pd.DataFrame([data])
            final_df.to_excel(excel_file, index=False)
            time.sleep(10)
        except Exception as e:
            data = {
                "Product_Name": "Details not available for this location",
                "Brand": "Details not available for this location",
                "MRP_Price": "Details not available for this location",
                "Final_Selling_Price": "Details not available for this location",
                "Store_Address": "Details not available for this location",
                "Variants": ["Details not available for this location"],
                "Product_URL": "Details not available for this location",
                "Input_Pincode": pincode
            }
            if os.path.exists(excel_file):
                existing_df = pd.read_excel(excel_file)
                new_df = pd.DataFrame([data])
                final_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                final_df = pd.DataFrame([data])
            final_df.to_excel(excel_file, index=False)
            time.sleep(10)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(15)
        exit()

base_url = "https://www.swiggy.com/instamart/item/{}?storeId=1402050"
options = webdriver.ChromeOptions()
options.add_argument('--headless=new')  
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
for pincode in data['pincodes']:
    location_entry(pincode, driver)
    for products in data['products']:
        url = base_url.format(products)
        data_scraper(pincode, url, driver)
    driver.get("https://www.swiggy.com/")
    driver.delete_all_cookies()
    driver.refresh()
