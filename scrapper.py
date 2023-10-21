from bs4 import BeautifulSoup
import os
import random
import re
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import signal
import sys
import time

from database import setup_csv, write_to_csv, get_tender_ids

PATH = "C:\Users\HP\OneDrive\Desktop\Bihar_web_Scrapper\chromedriver.exe"

URL = 'https://bidassist.com/'
CHROMEDRIVER_PATH = os.path.join(os.getcwd(), 'chromedriver', 'chromedriver')
OTP_REGEX = re.compile(r"^\d{6}$")
MOBILE_NO_REGEX = re.compile(r"^\d{10}$")

driver = None
tender_counter = 1


def sign_in(driver: WebDriver):
    driver.get(URL)
    wait = WebDriverWait(driver, 30)
    sign_in_xpath = "//*[@id=\"page-container\"]/div[2]/div/div[1]/div[1]/div[2]/header/div[2]/a"
    wait.until(EC.presence_of_element_located((By.XPATH, sign_in_xpath)))
    driver.find_element_by_xpath(sign_in_xpath).click()
    mobile_no_box_xpath = "//*[@id=\"tfid-13-0\"]"
    wait.until(
        EC.presence_of_element_located((By.XPATH, mobile_no_box_xpath)))
    print("Trying to sign in to BidAssist...")
    driver.find_element_by_xpath(
        "//*[@id=\"mobile-num\"]/form/div[1]/div[3]/div/div/div/label/span").click()
    driver.find_element_by_xpath(
        "//*[@id=\"mobile-num\"]/form/div[1]/div[4]/div/div/div/label/span").click()
    mobile_no = take_input(MOBILE_NO_REGEX, "Enter mobile number: ")
    if mobile_no is None:
        driver.close()
        return
    driver.find_element_by_xpath(mobile_no_box_xpath).send_keys(mobile_no)
    send_otp_btn_xpath = "//*[@id=\"mobile-num\"]/form/div[2]/button"
    wait.until(EC.presence_of_element_located(
        (By.XPATH, send_otp_btn_xpath)))
    driver.find_element_by_xpath(send_otp_btn_xpath).click()
    submit_otp_btn_xpath = "//*[@id=\"signin-form\"]/form/div[2]/div/button"
    wait.until(
        EC.presence_of_element_located((By.XPATH, submit_otp_btn_xpath)))
    otp = take_input(OTP_REGEX, "Enter OTP: ")
    if otp is None:
        driver.close()
        return
    driver.find_element_by_xpath("//*[@id=\"signin-otp\"]").send_keys(otp)
    driver.find_element_by_xpath(submit_otp_btn_xpath).click()
    try:
        # In case of Login Limit Reached
        ok_btn = "//*[@id=\"app-body\"]/div[22]/div/div/div/section/div/button[2]"
        wait.until(
            EC.presence_of_element_located((By.XPATH, ok_btn)))
        driver.find_element_by_xpath(ok_btn).click()
    except:
        pass
    try:
        # In case notification popup comes
        no_thanks_btn = "//*[@id=\"wzrk-cancel\"]"
        wait.until(
            EC.presence_of_element_located((By.XPATH, no_thanks_btn)))
        driver.find_element_by_xpath(no_thanks_btn).click()
    except:
        pass
    try:
        driver.find_element_by_xpath(
            "//*[@id=\"app-body\"]/div[9]/div/div/a").click()
    except:
        pass

    # Return positive result
    print(
        f"Successfully signed in to BidAssist with mobile number {mobile_no}")
    return True


def browse_through(driver: WebDriver):
    wait = WebDriverWait(driver, 30)
    search_kw = ' '.join(sys.argv[1:])

    if not bool(search_kw):
        indian_tenders_btn_xpath = "//*[@id=\"page-container\"]/div[2]/div/div[1]/div[1]/div[2]/header/div[2]/ul/li[2]/div/div[1]/span[1]/h4"
        wait.until(
            EC.presence_of_element_located((By.XPATH, indian_tenders_btn_xpath)))
        time.sleep(2)
        driver.find_element_by_xpath(indian_tenders_btn_xpath).click()
        # Select all in the dropdown list
        driver.find_element_by_xpath(
            "//*[@id=\"page-container\"]/div[2]/div/div[1]/div[1]/div[2]/header/div[2]/ul/li[2]/div/div[3]/ul/li[1]/a").click()
    else:
        print(f"Searching for {search_kw}...")
        # Type the search keyword
        driver.find_element_by_xpath(
            "//*[@id=\"page-container\"]/div[3]/div/div/div[1]/div[2]/div/div[2]/div/div/div[1]/input").send_keys(search_kw)
        time.sleep(1)
        # Click on search button
        driver.find_element_by_xpath(
            "//*[@id=\"page-container\"]/div[3]/div/div/div[1]/div[2]/div/div[2]/button/span").click()
    try:
        # In case guide pops up
        skip_btn_xpath = "//*[@id=\"react-joyride-step-0\"]/div/div/div/div[1]/div[2]/div/button"
        wait.until(
            EC.presence_of_element_located((By.XPATH, skip_btn_xpath)))
        driver.find_element_by_xpath(skip_btn_xpath).click()
    except:
        pass
    archived_btn = "//*[@id=\"page-container\"]/div[2]/div[2]/div[1]/div[1]/div/ul/li[2]/a/div/div[1]/span[1]/span[1]"
    wait.until(
        EC.presence_of_element_located((By.XPATH, archived_btn)))
    # Click on archieved button
    driver.find_element_by_xpath(archived_btn).click()

    # Find yearly dropdown list
    year_elements_xpath = "//*[@id=\"page-container\"]/div[2]/div[2]/div[1]/div[1]/div/ul/li[2]/a/div/div[3]/ul/li"
    y_nos = len(driver.find_elements_by_xpath(year_elements_xpath))

    for no in range(1, y_nos + 1):
        # Click year on dropdown link
        driver.find_element_by_xpath(
            year_elements_xpath + "[" + str(no) + "]").click()
        time.sleep(5)

        # Find total avl pages
        page_nos = int(driver.find_element_by_xpath(
            "//*[@id=\"page-container\"]/div[2]/div[2]/div[1]/div[2]/div/div/div[3]/ul/li[6]/a").text)

        # Loop through all pages
        for page in range(1, page_nos + 1):
            open_tender_pages(driver, page)
            # Go to next page if possible
            if page == page_nos:
                break
            driver.find_element_by_class_name("next").click()
            time.sleep(10)

    return True


def open_tender_pages(driver: WebDriver, page_no: int):
    wait = WebDriverWait(driver, 30)
    wait.until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "anchor-wrap")))
    tender_btns = driver.find_elements_by_class_name("anchor-wrap")
    tender_btn_count = len(tender_btns)
    btn_counter = 0
    main_window = driver.current_window_handle
    while btn_counter < tender_btn_count:
        try:
            tender_btns[btn_counter].send_keys(Keys.CONTROL + Keys.ENTER)
            driver.switch_to.window(driver.window_handles[1])
        except exceptions.StaleElementReferenceException:
            tender_btns = driver.find_elements_by_class_name("anchor-wrap")
            tender_btn_count = len(tender_btns)
            continue
        try:
            wait.until(EC.presence_of_all_elements_located(
                (By.TAG_NAME, "div")))
            wait.until(EC.presence_of_all_elements_located(
                (By.TAG_NAME, "span")))
            capture_data(str(driver.page_source))
        except:
            pass
        driver.close()
        btn_counter += 1
        driver.switch_to.window(main_window)


def capture_data(page_source):
    page = BeautifulSoup(page_source, 'html.parser')
    data = []
    global tender_counter

    # Capture the tender ID & tender no
    list_elem = page.find_all(
        'div', {'class': 'panel-body contact'})[1].find_all('li')
    for elem in list_elem[:2]:
        try:
            data.append(clean_text(elem.find('span').text))
        except:
            data.append(None)

    # Capture the title
    data.append(clean_text(
        page.find('div', {'class': 'panel-body application-header'}).find('h2').text))

    # Capture Opening Date, Closing Date and Tender Amount
    try:
        date_amt_elems = page.find(
            'ul', {'class': 'horizontal-items'}).find_all('li')[:3]
    except:
        return False
    for elem in date_amt_elems:
        item = clean_text(elem.find('p').text)

        # Fix the tender amount datatype
        if item is not None:
            if '\u20b9' in item:
                item = float(item.replace(
                    '\u20b9', '').replace(',', '').strip())

        data.append(item)

    # Capture the website
    data.append(clean_text(
        list_elem[-1].find('span').text))

    # Capture the location
    location = ''
    try:
        # Get the city name if available
        location += clean_text(page.find('a',
                               {'data-vars-event-action': 'view city'}).text) + ', '
    except:
        pass
    finally:
        # Get the state name
        location += clean_text(page.find('a',
                               {'data-vars-event-action': 'view state'}).text)
    data.append(location)

    # Write to csv file if does not exist
    if data[0] in get_tender_ids():
        print(f'Skipping Tender ID: {data[0]}')
        return
    write_to_csv(data)
    print(f'{tender_counter}: Captured data for Tender ID: {data[0]}')
    tender_counter += 1


def take_input(regex, text: str = None, retry_count: int = 2):
    ip = input(f"{text}")
    if regex.match(ip):
        return ip
    if retry_count > 0:
        return take_input(regex, text, retry_count - 1)


def random_time():
    return random.randint(1, 5)


def clean_text(text: str):
    return ' '.join(filter(lambda x: x, text.replace('\n', ' ').split()))


def main():
    options = webdriver.ChromeOptions()
    options.arguments.append("--window-size=1920x1080")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.headless = False
    setup_csv()
    global driver
    print("Launching browser...")
    driver = webdriver.Chrome(
        executable_path=CHROMEDRIVER_PATH, options=options)
    driver.implicitly_wait(10)
    print("Launched browser!")

    # Interrupt the program with Ctrl+C
    signal.signal(signal.SIGINT, lambda signal,
                  frame: signal_handler(signal, frame, driver))

    sign_in(driver)
    browse_through(driver)

    time.sleep(5)
    # driver.quit()


def signal_handler(signal, frame, driver: WebDriver):
    print('Exiting...')
    driver.quit()
    sys.exit(0)


if __name__ == '__main__':
    main()
