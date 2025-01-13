import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
from config import Config
from datetime import datetime
from fuzzywuzzy import fuzz
import os

class Workday:
  def __init__(self, url):
    self.url = url
    self.config = Config('config/profile.yaml')
    self.profile = self.config.profile
    self.companies_file = self.config.companies_file
    self.driver = webdriver.Chrome()  # You need to have chromedriver installed
    self.wait = WebDriverWait(self.driver, 10)
    self.driver.maximize_window()

    # Modified data structure: list of tuples (keywords, action)
    self.questionsToActions = [
        (["how did you hear about us"], self.handle_multiselect, ["Social Media", "LinkedIn"]),
        (["Are you legally eligible to work"], self.answer_dropdown, "Yes" ),
        (["Do you now or will you in the future require sponsorship for a work visa"], self.answer_dropdown, "No" ),
        (["have you previously been employed", "have you ever worked for"],  self.select_radio, "No"),
        (["country"],  self.answer_dropdown, "United States of America"),
        (["first name"],  self.fill_input, self.profile['first_name'],),
        (["last name"],  self.fill_input, self.profile['family_name']),
        (["email"],  self.fill_input, self.profile['email']),
        (["phone device type"],  self.answer_dropdown, "Mobile"),
        (["country phone code"],  self.answer_dropdown, "United States (+1)"),
        (["phone number"],  self.fill_input, self.profile['phone_number']),
        (["are you legally authorized"],  self.select_radio, "Yes"),
        (["will you now or in the future"],  self.select_radio, "No"),
        (["do you require sponsorship"],  self.select_radio, "No"),
        (["disability status"],  self.select_radio, "I don't wish to answer"),
        (["veteran status"],  self.answer_dropdown, "I am not"),
        (["gender"],  self.answer_dropdown, "Male"),
        (["ethnicity"],  self.answer_dropdown, "Black or African American (United States of America)"),
        (["hispanic or latino"],  self.select_radio, "No"),
        (["date"],  self.handle_date, None),
        (["Please check one of the boxes below: "],  self.select_checkbox, None),
        (["I understand and acknowledge the terms of use"],  self.select_checkbox, None),
    ]
  def handle_date(self, element, _):
    month_input = element.find_element(By.CSS_SELECTOR, "div[dateSectionMonth-display='dateSectionMonth-display']")
    day_input = element.find_element(By.CSS_SELECTOR, "div[dateSectionDay-display='dateSectionDay-display']")
    year_input = element.find_element(By.CSS_SELECTOR, "div[dateSectionYear-display='dateSectionYear-display']")
    self.wait.until(EC.element_to_be_clickable(month_input))
    self.wait.until(EC.element_to_be_clickable(day_input))
    self.wait.until(EC.element_to_be_clickable(year_input))
    month_input.send_keys(datetime.now().strftime("%m"))
    day_input.send_keys(datetime.now().strftime("%d"))
    year_input.send_keys(datetime.now().strftime("%Y"))
  def signup(self):
    print("Signup")
    try:
      self.wait.until(EC.element_to_be_clickable((By.XPATH, "input[@type='checkbox']")))
      self.driver.find_element(By.XPATH, "input[@type='checkbox']").click()
    except TimeoutException:
      print("Exception: 'No button for Signup'")
    time.sleep(5)
    try:
      self.driver.find_element(By.CSS_SELECTOR, "input[type='text'][data-automation-id='email']").send_keys(self.profile['email'])
      self.driver.find_element(By.CSS_SELECTOR, "input[type='password'][data-automation-id='password']").send_keys(self.profile['password'])
      self.driver.find_element(By.CSS_SELECTOR, "input[type='password'][data-automation-id='verifyPassword']").send_keys(self.profile['password'])
    # try:
    #   self.driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][data-automation-id='createAccountCheckbox']").click()
    # except:
    #   print("Exception: 'There is no checkbox for signup'")
      button = self.driver.find_element(By.CSS_SELECTOR, "div[role='button'][aria-label='Create Account'][data-automation-id='click_filter']")
      self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='button'][aria-label='Create Account'][data-automation-id='click_filter']")))
      time.sleep(1)
      button.click()
      time.sleep(2)
    
    except Exception as e:
      print("Exception: 'Signup failed'", e)
  
  def signin(self):
    print("Signin")
    try:
        self.driver.find_element(By.CSS_SELECTOR, "input[type='text'][data-automation-id='email']").send_keys(self.profile['email'])
        self.driver.find_element(By.CSS_SELECTOR, "input[type='password'][data-automation-id='password']").send_keys(self.profile['password'])
        button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='button'][aria-label='Sign In'][data-automation-id='click_filter']")))
        time.sleep(1)
        button.click()
    except Exception as e:
      print("Exception: 'Signin failed'", e)

  def find_next_sibling_safely(self, start_element, max_levels=3):
    """
    Safely navigate up the DOM tree and find the next sibling div,
    checking for elements at each level before proceeding.
    
    Args:
        start_element: WebElement - The starting element
        max_levels: int - Maximum number of levels to traverse up
    
    Returns:
        tuple: (WebElement or None, int) - Found element and levels traversed
    """
    try:
        current = start_element
        for level in range(max_levels):
            # First check if there's a sibling at current level
            siblings = current.find_elements(By.XPATH, "./following-sibling::div[@data-automation-id]")
            if siblings:
                print(f"Found sibling at level {level}")
                return siblings[0], level
            
            # If no siblings, try to go up one level
            try:
                parent = current.find_element(By.XPATH, "./..")
                # Verify we actually moved up (parent should be different from current)
                if parent.id == current.id:
                    print(f"Reached same element at level {level}, stopping")
                    return None, level
                current = parent
            except:
                print(f"Cannot go up from level {level}")
                return None, level
                
        return None, max_levels
        
    except Exception as e:
        print(f"Error in safe navigation: {e}")
        return None, 0
  def fillform_page_1(self):
    try:
      self.driver.find_element(By.CSS_SELECTOR, "input[data-automation-id='file-upload-input-ref']").send_keys(self.profile['resume_path'])
      time.sleep(1)
    except Exception as e:
      print("Exception: 'Missmatch in order'", e)
      return False
    return True
  def handle_questions(self):
    required_fields = self.driver.find_elements(By.XPATH, "//abbr[text()='*']")
    questions = []
    print(f"\nFound {len(required_fields)} required fields")
      
    for field in required_fields[1:]:
      try:
        # Get the parent span containing the question text
        question = field.find_element(By.XPATH, "./..")
        question_text = question.text
        if not question_text:
          continue
        container, levels_traversed = self.find_next_sibling_safely(question)
        print("question tag name", question.tag_name, question.text)
        # Get the parent div that would contain both question and input area
        print(f"Container class: {container.get_attribute('class')}")
        # Find any element with data-automation-id within this container
        input_field = container.find_element(By.CSS_SELECTOR, "[data-automation-id]")
        automation_id = input_field.get_attribute('data-automation-id')
        print(f"Input_field: {input_field.get_attribute('data-automation-id')}")
        print(f"\nQuestion: {question_text}")
        print(f"Element automation-id: {automation_id}")
        print(f"input field: {input_field}")
        questions.append((question_text, input_field, automation_id))
      except Exception as e:
        print(f"Error processing field: {e}")
        continue
      
    for question_text, input_element, automation_id in questions:
      handled = False
      best_match_score = 0
      best_match_action = None
      best_match_value = None
      
      for keywords, action, value in self.questionsToActions:
          for keyword in keywords:
              score = fuzz.partial_ratio(question_text.lower(), keyword.lower())
              if score > best_match_score:
                  best_match_score = score
                  best_match_action = action
                  best_match_value = value
      
      if best_match_score > 75:  # Set a threshold for what you consider a "match"
            print(f"Executing action for question: {question_text} with best match score of: {best_match_score}, {best_match_value}")
            action_result = best_match_action(input_element, input_element.get_attribute('data-automation-id'), values=best_match_value) if best_match_value is not None else best_match_action(input_element.get_attribute('data-automation-id'))
            time.sleep(6)
            if action_result:
                  print(f"Action successful: {best_match_action}")
            else:
                  print(f"Action failed: {best_match_action}")
            handled = True
      
      if not handled:
          print(f"No matching action found for question: {question_text}. Please fill manually")

    print(f"\nSuccessfully processed {len(questions)} questions")
    print("\nQuestions found:")
    for q, i, aid in questions:
      print(f"Q: {q} -> automation-id: {aid}")
    input("Press Enter to continue after reviewing the questions...")
    return True
    
  def fillform_page_2(self):
    try:
      time.sleep(2)
      res = self.handle_questions()
      return res 
    except Exception as e:
      print(f"Exception in form page 2: {e}")
      input("Press Enter when you've fixed the issues and are ready to continue...")
      return False

  def fillform_page_4(self):
    try:
      return self.handle_questions()
    except Exception as e:
      print(f"Exception in form page 4: {e}")
      input("Press Enter when you've fixed the issues and are ready to continue...")
      return False
    
  def click_next(self):
    button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-automation-id='bottom-navigation-next-button']")))
    button.click()
    try:
      error_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-automation-id='errorBanner']")
      print("Exception: 'Errors on page. Please resolve and submit manually. You have 60 seconds to do so!'")
      time.sleep(60)
    except:
      print("No Errors")
    time.sleep(10)
    
  def apply(self, company):
    try:
      parsed_url = urlparse(self.url)
      company = parsed_url.netloc.split('.')[0]
      existing_company = company in self.config.read_companies()
      self.driver.get(self.url) # Open a webpage
      time.sleep(4)
        
      # Try to click the Apply button
      try:
          apply_button = self.driver.find_element(By.CSS_SELECTOR, "a[role='button'][data-uxi-element-id='Apply_adventureButton']")
          apply_button.click()
          time.sleep(2)
      except Exception as e:
          print("No Apply button found, continuing...", e)
      
      # Try autofill with resume
      try:
          button = self.driver.find_element(By.CSS_SELECTOR, "a[role='button'][data-automation-id='autofillWithResume']")
          button.click()
          time.sleep(2)
      except Exception as e:
          print("No autofill resume button found", e)
          
      print("existing_company:", existing_company)
      if existing_company:
          self.signin()
      else:
          self.signup()
          self.companies_file.write_company(company)
      p_tags = self.driver.find_elements(By.XPATH, "//p[contains(text(), 'verify')]")
      if len(p_tags) > 0:
        print("Verification needed")
        input("Please verify your account and press Enter when you're ready to continue...")
      step1 = self.fillform_page_1()
      if not step1:
        input("Press Enter when you're ready to continue with page 1...")
      self.click_next()
      
      step2 = self.fillform_page_2()
      if not step2:
        input("Press Enter when you're ready to continue with page 2...")
      self.click_next()
      self.click_next()
      # step3 = self.fillform_page_3()
      # if not step3:
      #   input("Press Enter when you're ready to continue with page 3...")
      step4 = self.fillform_page_4()
      if not step4:
        input("Press Enter when you're ready to continue with page 4...")
      self.click_next()
      
      step5 = self.fillform_page_4()
      if not step5:
        input("Press Enter when you're ready to continue with page 5...")
      self.click_next()
      step5 = self.fillform_page_4()
      if not step5:
        input("Press Enter when you're ready to continue with page 5...")
      self.click_next()
            
      self.click_next()
      
      # review and submit
      self.click_next()
      
      self.driver.quit()
      return True
    except Exception as e:
      print(f"Exception in application process: {e}")
      input("Press Enter when you've fixed the issues and are ready to continue...")
      return False

  def handle_multiselect(self, element, _, values=[]):
    """Handle multi-select dropdowns that require multiple clicks"""
    try:
      # Click to open the dropdown
      element.click()
      time.sleep(1)
      
      # Click each selection in order
      for selection in values:
        self.driver.find_element(By.XPATH, f"//div[text()='{selection}']").click()
        time.sleep(1)
      return True
    except Exception as e:
      print(f"Error in handle_multiselect: {e}")
      return False

  def answer_dropdown(self, element, _, values=""):
    """Handle single-select dropdowns"""
    try:
        print("value being selected", values)
        # Click to open the dropdown
        self.driver.execute_script("arguments[0].click();", element)
        time.sleep(1)
        
        # Find all options and look for a case-insensitive match
        options = self.driver.find_elements(By.CSS_SELECTOR, "ul[role='listbox'] li[role='option'] div")
        for option in options:
            print("values:", values.lower(),option.text.lower())
            if option.text.lower() == values.lower() or option.text.lower().startswith(values.lower()):
                self.driver.execute_script("arguments[0].click();", option)
                time.sleep(1)
                return True
                
        print(f"Could not find option: {values}")
        print("Available options:", [opt.text for opt in options])
        return False
        
    except Exception as e:
        print(f"Error in answer_dropdown: {e}")
        return False

  def fill_input(self, element, data_automation_id, values=[]):
    """Handle text input fields"""
    current_value = element.get_attribute('value')
    if current_value == str(values):
        print(f"Field already has correct value: {values}")
        return True
    try:
      print(f"Input value: {values}")
      # Clear the existing value
      element.clear()
      time.sleep(1)
      element = self.driver.find_element(By.CSS_SELECTOR, f"input[data-automation-id='{data_automation_id}']")
      element.send_keys(values)
      time.sleep(1)
      return True
    except Exception as e:
      print(f"Error in fill_input: {e}")
      return False
  def select_checkbox(self, element, data_automation_id):
    radio_button = radio_options.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')
    wait.until(EC.element_to_be_clickable(radio_button))
    radio_button.click()

  def select_radio(self, element, data_automation_id, values="", checkbox=False):
    """
    Handle radio button selections with the specific Workday HTML structure
    """
    try:
        print(f"Selecting radio value: {values} for automation-id: {data_automation_id}")
        
        # Find the container with the radio group
        radio_group = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f'div[data-automation-id="{data_automation_id}"]'))
        )
        
        # Find all radio options within the group
        radio_options = radio_group.find_elements(By.CSS_SELECTOR, 'div[class*="css-1utp272"]')
        for option in radio_options:
            try:
                # Get the label text to match against our value
                label = option.find_element(By.CSS_SELECTOR, 'label').text.strip()
                
                if values.lower() in label.lower():
                    # Find the actual radio input within this option
                    radio_input = option.find_element(By.CSS_SELECTOR, 'input[type="radio"]')
                    
                    # Try to click the label first (often more reliable than clicking the input directly)
                    try:
                        option.find_element(By.CSS_SELECTOR, 'label').click()
                    except:
                        # If label click fails, try JavaScript click on the input
                        self.driver.execute_script("arguments[0].click();", radio_input)
                    
                    time.sleep(1)
                    return True
            except Exception as e:
                print(f"Error with option: {e}")
                continue
        
        print(f"No matching radio option found for value: {value}")
        print("Available options:", [opt.find_element(By.CSS_SELECTOR, 'label').text for opt in radio_options])
        return False
        
    except Exception as e:
        print(f"Error in select_radio: {e}")
        return False

def main():
    # Path to jobs.txt file
    jobs_file = os.path.join(os.path.dirname(__file__), 'config', 'jobs.txt')
    
    if not os.path.exists(jobs_file):
        print(f"Error: {jobs_file} not found!")
        return
    
    # Read and process URLs from jobs.txt
    with open(jobs_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not urls:
        print("No URLs found in jobs.txt. Please add some job URLs to the file.")
        return
    
    print(f"Found {len(urls)} jobs to apply for:")
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")
    
    print("\nStarting application process...")
    
    for i, url in enumerate(urls, 1):
        print(f"\nProcessing job {i}/{len(urls)}: {url}")
        try:
            workday = Workday(url)
            workday.apply(url)
            print(f"Completed job {i}/{len(urls)}")
        except Exception as e:
            print(f"Error processing job {url}: {e}")
        print("\nWaiting 30 seconds before next application...")
        time.sleep(30)
    
    print("\nAll jobs processed!")

if __name__ == "__main__":
    main()
