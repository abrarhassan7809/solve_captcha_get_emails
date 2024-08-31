import os
# from selenium import webdriver
import undetected_chromedriver as webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image


def get_canvas_image(driver, canvas_element):
    canvas_base64 = driver.execute_script("""
        var canvas = arguments[0];
        return canvas.toDataURL('image/png').substring(22);
    """, canvas_element)

    canvas_bytes = base64.b64decode(canvas_base64)
    image = Image.open(BytesIO(canvas_bytes))
    return image


def save_image(image, folder, filename):
    if not os.path.exists(folder):
        os.makedirs(folder)
    image_path = os.path.join(folder, filename)
    image.save(image_path)
    print(f"Image saved to {image_path}")


def preprocess_image(image):
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return thresh


def find_gap_position(slider_image, background_image):
    slider_gray = cv2.cvtColor(np.array(slider_image), cv2.COLOR_BGR2GRAY)
    background_gray = cv2.cvtColor(np.array(background_image), cv2.COLOR_BGR2GRAY)

    # Increase the number of features
    orb = cv2.ORB_create(nfeatures=1000)
    kp1, des1 = orb.detectAndCompute(slider_gray, None)
    kp2, des2 = orb.detectAndCompute(background_gray, None)

    # Use FLANN-based matcher for better results
    index_params = dict(algorithm=6,  # FLANN_INDEX_LSH
                        table_number=6,  # 12
                        key_size=12,  # 20
                        multi_probe_level=2)  # 2
    search_params = dict(checks=50)  # Increase this to improve accuracy
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    # Perform the matching with k=2
    matches = flann.knnMatch(des1, des2, k=2)

    # Apply ratio test to filter matches
    good_matches = []
    for match in matches:
        if len(match) == 2:
            m, n = match
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)

    if len(good_matches) == 0:
        print("No good matches found.")
        return None

    # Visualize the matches
    img_matches = cv2.drawMatches(slider_gray, kp1, background_gray, kp2, good_matches, None,
                                  flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    save_image(Image.fromarray(img_matches), "captcha_images", "flann_matches.png")

    # Calculate the average position of the best matches
    gap_position = np.mean([kp1[m.queryIdx].pt[0] for m in good_matches])
    print('Number of good matches:', len(good_matches), 'Gap position:', gap_position)
    return int(gap_position)

def solve_slider_captcha(driver):
    try:
        driver.get('https://www.chileautos.cl/vehiculos/autos-vehículo/?sort=MakeModel&offset=1')
        wait = WebDriverWait(driver, 20)
        print('Start')

        # Switch to captcha iframe if present
        if driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha')]"):
            iframe = driver.find_element(By.XPATH, "//iframe[contains(@src, 'captcha')]")
            driver.switch_to.frame(iframe)
            print('Switched to captcha iframe')
            time.sleep(1)

        # Locate the slider and the puzzle canvas
        print('Looking for slider...')
        slider = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='captcha__frame__bottom']//div[@class='slider']")))
        print('Slider found')
        time.sleep(1)

        # Capture the images from the canvas
        puzzle_canvas = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='captcha__puzzle']//canvas[1]")))
        background_canvas = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='captcha__puzzle']//canvas[2]")))
        puzzle_image = get_canvas_image(driver, puzzle_canvas)
        background_image = get_canvas_image(driver, background_canvas)
        time.sleep(1)

        # Save the captured images for verification
        save_image(puzzle_image, "captcha_images", "puzzle_image.png")
        save_image(background_image, "captcha_images", "background_image.png")
        time.sleep(1)

        # Find the gap position in the background
        gap_position = find_gap_position(puzzle_image, background_image)
        print(f'Gap position found at: {gap_position}')
        time.sleep(1)

        if gap_position is None:
            return False

        # Calculate the offset required to move the slider
        move_offset = gap_position
        print(f'Moving slider by offset: {move_offset}')

        # Begin moving the slider
        action = ActionChains(driver)
        action.click_and_hold(slider).perform()
        print('Slider click and hold performed')
        time.sleep(1)

        # Move the slider by the calculated offset
        action.move_by_offset(move_offset, 0).perform()
        time.sleep(1)

        # Release the slider
        action.release().perform()
        print('Slider released')

        # Wait for the captcha to be verified
        time.sleep(5)

        # Check if captcha was solved successfully
        if "Verification failed" in driver.page_source or driver.find_elements(By.CLASS_NAME, 'retry-container'):
            print("Captcha verification failed. Retrying...")
            return False

        print("Captcha solved successfully.")
        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        return False

    finally:
        driver.switch_to.default_content()


# Usage example
if __name__ == "__main__":
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--use_subprocess")
    driver = webdriver.Chrome(options=options)
    if solve_slider_captcha(driver):
        print("Proceeding with further actions...")
    else:
        print("Exiting due to failed captcha.")

    driver.quit()