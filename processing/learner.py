import json
import os
import time
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class InteractionLearner:
    """
    A more sophisticated learning system that observes actual DOM changes and network 
    activity when automation fails and the user manually intervenes.
    """
    def __init__(self, driver, learning_file="./config/learned_interactions.json"):
        self.driver = driver
        self.learning_file = learning_file
        self.learning_data = self._load_learning_data()
        self.snapshot_before = None
        self.network_logs = []
        self.observation_active = False
        self.current_element = None
        self.current_question = None
        
    def _load_learning_data(self):
        """Load existing learning data from file if it exists"""
        if os.path.exists(self.learning_file):
            try:
                with open(self.learning_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("Error loading learning data, creating new file")
                return self._create_empty_data()
        else:
            return self._create_empty_data()
    
    def _create_empty_data(self):
        return {
            "learned_questions": [],
            "observed_interactions": [],
            "network_logs": [],
            "failed_attempts": []
        }
    
    def save_learning_data(self):
        """Save learning data to file"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.learning_file), exist_ok=True)
        
        with open(self.learning_file, 'w') as f:
            json.dump(self.learning_data, f, indent=2)
        print(f"Saved learning data to {self.learning_file}")
    
    def start_observation(self, element, question_text, element_type):
        """
        Start observing an element for changes when the user manually intervenes
        """
        print("\n" + "="*80)
        print(f"LEARNING MODE ACTIVATED for question: '{question_text}'")
        print("Please manually fill out this field. The system will observe your interaction.")
        print("="*80 + "\n")
        
        self.observation_active = True
        self.current_element = element
        self.current_question = question_text
        
        # Take before snapshot of the element and its state
        self.snapshot_before = self._capture_element_state(element)
        
        # Capture initial XHR state if possible
        self._capture_network_state()
        
        # Set up a mutation observer using JavaScript
        self._setup_mutation_observer(element)
    
    def _setup_mutation_observer(self, element):
        """Set up a JavaScript mutation observer to track DOM changes"""
        observer_script = """
        // Store the original XHR open and send methods
        const originalOpen = XMLHttpRequest.prototype.open;
        const originalSend = XMLHttpRequest.prototype.send;
        
        // Global array to store XHR information
        window.xhrCaptures = [];
        
        // Override the open method
        XMLHttpRequest.prototype.open = function() {
            this._method = arguments[0];
            this._url = arguments[1];
            return originalOpen.apply(this, arguments);
        };
        
        // Override the send method
        XMLHttpRequest.prototype.send = function() {
            const xhr = this;
            const startTime = new Date().getTime();
            
            // Add event listener for when the request completes
            this.addEventListener('load', function() {
                const endTime = new Date().getTime();
                const captureObj = {
                    method: xhr._method,
                    url: xhr._url,
                    status: xhr.status,
                    duration: endTime - startTime,
                    responseType: xhr.responseType,
                    timestamp: new Date().toISOString()
                };
                
                // Try to capture response data if it's not binary
                if (xhr.responseType === '' || xhr.responseType === 'text') {
                    captureObj.response = xhr.responseText;
                } else {
                    captureObj.response = "[" + xhr.responseType + " data]";
                }
                
                // Store the capture
                window.xhrCaptures.push(captureObj);
            });
            
            return originalSend.apply(this, arguments);
        };
        
        // Return true to indicate script was executed
        true;
        """
        
        try:
            # Execute the XHR capture setup
            self.driver.execute_script(observer_script)
            print("Network monitoring activated")
        except Exception as e:
            print(f"Error setting up network monitoring: {e}")
    
    def _capture_element_state(self, element):
        """Capture the current state of an element"""
        try:
            state = {
                "html": element.get_attribute("outerHTML"),
                "is_displayed": element.is_displayed(),
                "value": element.get_attribute("value"),
                "text": element.text,
                "classes": element.get_attribute("class"),
                "attributes": {}
            }
            
            # Capture all attributes
            attributes = self.driver.execute_script(
                "var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) "
                "{ items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;", 
                element
            )
            
            state["attributes"] = attributes
            
            # Capture parent context for better understanding
            try:
                parent = element.find_element(By.XPATH, "./..")
                state["parent_html"] = parent.get_attribute("outerHTML")
            except:
                state["parent_html"] = None
                
            return state
        except Exception as e:
            print(f"Error capturing element state: {e}")
            return {"error": str(e)}
    
    def _capture_network_state(self):
        """Capture the current network state"""
        try:
            # Clear any existing captures
            self.driver.execute_script("window.xhrCaptures = [];")
            self.network_logs = []
        except Exception as e:
            print(f"Error resetting network capture: {e}")
    
    def _get_network_activity(self):
        """Get all captured XHR activity"""
        try:
            xhrs = self.driver.execute_script("return window.xhrCaptures;")
            return xhrs if xhrs else []
        except Exception as e:
            print(f"Error getting network activity: {e}")
            return []
    
    def end_observation(self):
        """End observation and analyze what changed"""
        if not self.observation_active:
            return
            
        print("\n" + "="*80)
        print("ANALYZING USER INTERACTION...")
        
        # Wait a moment for any async operations to complete
        time.sleep(2)
        
        # Capture final element state
        snapshot_after = self._capture_element_state(self.current_element)
        
        # Get network logs
        network_logs = self._get_network_activity()
        
        # Analyze changes
        changes = self._analyze_changes(self.snapshot_before, snapshot_after)
        
        # Record the learned interaction
        self._record_interaction(changes, network_logs)
        
        print("LEARNING COMPLETE!")
        print("="*80 + "\n")
        
        # Reset observation state
        self.observation_active = False
        self.current_element = None
        self.current_question = None
        self.snapshot_before = None
        
        # Save the updated data
        self.save_learning_data()
    
    def _analyze_changes(self, before, after):
        """Analyze the changes between before and after states"""
        changes = {
            "value_changed": False,
            "classes_changed": False,
            "html_changed": False,
            "attribute_changes": {},
            "details": {}
        }
        
        # Check value change (for inputs)
        if before.get("value") != after.get("value"):
            changes["value_changed"] = True
            changes["details"]["value"] = {
                "before": before.get("value"),
                "after": after.get("value")
            }
        
        # Check class changes
        if before.get("classes") != after.get("classes"):
            changes["classes_changed"] = True
            changes["details"]["classes"] = {
                "before": before.get("classes"),
                "after": after.get("classes")
            }
        
        # Check HTML changes
        if before.get("html") != after.get("html"):
            changes["html_changed"] = True
        
        # Check attribute changes
        before_attrs = before.get("attributes", {})
        after_attrs = after.get("attributes", {})
        
        # Check which attributes changed
        for key in set(list(before_attrs.keys()) + list(after_attrs.keys())):
            if before_attrs.get(key) != after_attrs.get(key):
                changes["attribute_changes"][key] = {
                    "before": before_attrs.get(key),
                    "after": after_attrs.get(key)
                }
        
        return changes
    
    def _record_interaction(self, changes, network_logs):
        """Record the observed interaction"""
        # Determine what was actually entered/selected
        user_input = self._extract_user_input(changes)
        element_type = self._determine_element_type(changes, network_logs)
        action_type = self._determine_action_type(element_type, changes)
        
        # Create an observation record
        observation = {
            "timestamp": datetime.now().isoformat(),
            "question": self.current_question,
            "element_type": element_type,
            "action_type": action_type,
            "user_input": user_input,
            "changes": changes,
            "network_requests": [
                {
                    "url": log.get("url"),
                    "method": log.get("method"),
                    "status": log.get("status")
                } for log in network_logs[:5]  # Store only essential info for the first 5 logs
            ] if network_logs else []
        }
        
        # Add to learning data
        self.learning_data["observed_interactions"].append(observation)
        
        # Also add a more structured question mapping for easy retrieval
        question_mapping = {
            "timestamp": datetime.now().isoformat(),
            "question": self.current_question,
            "element_type": element_type,
            "action_type": action_type,
            "value": user_input
        }
        
        self.learning_data["learned_questions"].append(question_mapping)
        
        print(f"Learned interaction for question: '{self.current_question}'")
        print(f"  Element type: {element_type}")
        print(f"  Action type: {action_type}")
        print(f"  User input: {user_input}")
    
    def _extract_user_input(self, changes):
        """Extract what the user actually entered or selected"""
        # For text inputs, the value change is usually what matters
        if changes.get("value_changed"):
            return changes.get("details", {}).get("value", {}).get("after", "")
        
        # For dropdowns and selects, look for changes in selected attributes
        if changes.get("attribute_changes", {}).get("aria-selected") == "true":
            return self.current_element.text
            
        # For checkboxes and radios, check if they became checked
        if changes.get("attribute_changes", {}).get("checked") == "true":
            return "true"
            
        # If we can't determine, use the element's text as a fallback
        if self.current_element and self.current_element.text:
            return self.current_element.text
            
        return "unknown"
    
    def _determine_element_type(self, changes, network_logs):
        """Determine the type of element based on changes and network activity"""
        tag_name = self.current_element.tag_name.lower() if self.current_element else "unknown"
        
        # Check for input-specific attributes in changes
        if changes.get("value_changed"):
            return "text_input"
            
        if "checked" in changes.get("attribute_changes", {}):
            if tag_name == "input":
                input_type = self.current_element.get_attribute("type")
                return input_type if input_type else "checkbox"
                
        if "selected" in changes.get("attribute_changes", {}) or "aria-selected" in changes.get("attribute_changes", {}):
            return "dropdown"
            
        # Check tag names
        if tag_name == "select":
            return "dropdown"
            
        if tag_name == "input":
            input_type = self.current_element.get_attribute("type")
            if input_type:
                return input_type
        
        # Look at network requests for clues
        for log in network_logs:
            url = log.get("url", "").lower()
            if "dropdown" in url or "select" in url:
                return "dropdown"
            if "checkbox" in url:
                return "checkbox"
            if "radio" in url:
                return "radio"
            if "multiselect" in url:
                return "multiselect"
                
        # Default fallback based on class names or role attributes
        attrs = self.current_element.get_attribute("class") or ""
        role = self.current_element.get_attribute("role") or ""
        
        if "dropdown" in attrs.lower() or "select" in attrs.lower() or role == "combobox":
            return "dropdown"
        if "checkbox" in attrs.lower() or role == "checkbox":
            return "checkbox"
        if "radio" in attrs.lower() or role == "radio":
            return "radio"
        if "multiselect" in attrs.lower():
            return "multiselect"
            
        return "unknown"
    
    def _determine_action_type(self, element_type, changes):
        """Determine what action was performed based on element type and changes"""
        if element_type == "text_input":
            return "fill_input"
            
        if element_type in ["checkbox", "radio"]:
            return "select_radio" if element_type == "radio" else "select_checkbox"
            
        if element_type == "dropdown":
            return "answer_dropdown"
            
        if element_type == "multiselect":
            return "handle_multiselect"
            
        # If we can't determine, look at the types of changes
        if changes.get("value_changed"):
            return "fill_input"
            
        if changes.get("attribute_changes", {}).get("checked"):
            return "select_checkbox"
            
        if changes.get("attribute_changes", {}).get("selected") or changes.get("attribute_changes", {}).get("aria-selected"):
            return "answer_dropdown"
            
        return "unknown_action"
    
    def find_similar_question(self, question_text, threshold=0.7):
        """Find if a similar question has been learned before"""
        # First try exact match
        for mapping in self.learning_data["learned_questions"]:
            if mapping["question"].lower() == question_text.lower():
                return mapping
        
        # Then try partial matches
        best_match = None
        best_score = 0
        
        for mapping in self.learning_data["learned_questions"]:
            # Basic word overlap scoring
            stored_q = mapping["question"].lower()
            current_q = question_text.lower()
            
            words1 = set(stored_q.split())
            words2 = set(current_q.split())
            
            if not words1 or not words2:
                continue
                
            # Calculate Jaccard similarity
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            score = len(intersection) / len(union)
            
            # Boost score if key terms match exactly
            key_terms = ["name", "email", "address", "phone", "experience", "education", 
                        "skills", "salary", "sponsor", "eligible", "authorized"]
                        
            for term in key_terms:
                if term in stored_q and term in current_q:
                    score += 0.1  # Boost for matching important terms
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = mapping
        
        return best_match

    def record_failed_attempt(self, question_text, attempted_action, error):
        """Record a failed automation attempt"""
        failure = {
            "timestamp": datetime.now().isoformat(),
            "question": question_text,
            "attempted_action": attempted_action,
            "error": str(error)
        }
        
        self.learning_data["failed_attempts"].append(failure)
        self.save_learning_data()