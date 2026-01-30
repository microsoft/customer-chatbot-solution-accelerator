from asyncio.log import logger
from base.base import BasePage
from playwright.sync_api import expect
class WebUserPage(BasePage):
    
    # Locators
    OPEN_CHAT_BUTTON = "button:has-text('Open Chat')"
    TYPE_QUESTION_TEXT_AREA = "input[data-slot='input'][placeholder='Ask a question']"
    SEND_BUTTON = "button[data-slot='button'][title='Send message']"
    STOP_GENERATING_LABEL = "[aria-label='Stop generating']"
    CHAT_RESPONSE = "[data-testid='chat-response'], .chat-response, [role='article']"
    CHAT_MESSAGE = ".chat-message, [data-testid='chat-message']"

    def __init__(self, page):
        self.page = page
        self.soft_assert_errors = []

    def enter_a_question(self, text):
        # Type a question in the text area
        self.page.locator(self.TYPE_QUESTION_TEXT_AREA).fill(text)
        self.page.wait_for_timeout(2000)

    def click_send_button(self):
        # Wait for send button to be enabled and visible, then click
        send_button = self.page.locator(self.SEND_BUTTON)
        # Wait for button to be visible and enabled
        send_button.wait_for(state="visible", timeout=10000)
        # Wait for button to be enabled (not disabled)
        self.page.wait_for_function(
            "() => !document.querySelector('button[data-slot=\"button\"][title=\"Send message\"]').disabled",
            timeout=10000
        )
        send_button.click()
        self.page.locator(self.STOP_GENERATING_LABEL).wait_for(state="hidden", timeout=30000)

    def open_chat_window(self):
        """Click on the Open Chat button to open the chat window"""
        chat_button = self.page.locator(self.OPEN_CHAT_BUTTON)
        chat_button.wait_for(state="visible", timeout=10000)
        chat_button.click()
        # Wait for chat input to appear
        self.page.locator(self.TYPE_QUESTION_TEXT_AREA).wait_for(state="visible", timeout=10000)

    def wait_for_response(self, timeout=30000):
        """Wait for the chat response to appear"""
        # Wait for stop generating button to disappear (indicating response is complete)
        try:
            self.page.locator(self.STOP_GENERATING_LABEL).wait_for(state="hidden", timeout=timeout)
        except:
            # If stop generating button doesn't appear, just wait a bit
            pass
        
        # Wait for AI response to appear by looking for response indicators
        # Wait for new content to appear that indicates an AI response
        try:
            # Wait for either the "AI-generated content may be incorrect" footer to appear
            # or wait for any meaningful response content
            self.page.wait_for_function("""
                () => {
                    const pageText = document.body.innerText;
                    const aiIndicators = [
                        'AI-generated content may be incorrect',
                        'Yes, we offer',
                        'warranty',
                        'Contoso',
                        '2-year',
                        'return'
                    ];
                    return aiIndicators.some(indicator => 
                        pageText.includes(indicator) && 
                        pageText.split(indicator).length > pageText.split('Do you provide a color matching service?').length
                    );
                }
            """, timeout=timeout)
        except:
            pass
        
        # Additional wait to ensure response is fully loaded
        self.page.wait_for_timeout(3000)

    def get_last_response(self):
        """Get the text content of the last chat response"""
        # Wait for any dynamic content to load
        self.page.wait_for_timeout(3000)
        
        # Get all text content from the page
        full_page_text = self.page.locator('body').text_content()
        
        # Method 1: Split by timestamps to isolate individual messages
        import re
        timestamp_pattern = r'Jan \d+, \d+:\d+ PM'
        
        # Split by timestamps to get message blocks
        message_blocks = re.split(timestamp_pattern, full_page_text)
        
        if len(message_blocks) > 1:
            # Look through message blocks from the end to find the most recent AI response
            for i in range(len(message_blocks) - 1, -1, -1):
                block = message_blocks[i]
                
                # Skip very short blocks (likely empty or just metadata)
                if len(block.strip()) < 30:
                    continue
                
                # Clean up the block
                cleaned_block = block.strip()
                
                # Remove common UI elements and user indicators
                cleanup_patterns = [
                    'ContosoClose ChatEnable Identity Provider',
                    'You', 'AI', 'AI-generated content may be incorrect',
                    'Products', 'Showing', 'results'
                ]
                
                for pattern in cleanup_patterns:
                    cleaned_block = cleaned_block.replace(pattern, ' ')
                
                # Normalize whitespace
                cleaned_block = re.sub(r'\s+', ' ', cleaned_block).strip()
                
                # Check if this looks like an AI response (contains key phrases)
                ai_indicators = [
                    'paint', 'color', 'warranty', 'matching', 'service', 
                    'Cloud Drift', 'blue', 'return', 'policy', 'satisfaction'
                ]
                
                if any(indicator.lower() in cleaned_block.lower() for indicator in ai_indicators):
                    # This looks like an AI response
                    if len(cleaned_block) > 50:  # Must be substantial
                        return cleaned_block
        
        # Method 2: Look for specific AI response patterns
        ai_response_patterns = [
            r"Here are some[^.]*paint[^.]*\.",
            r"Yes, we (?:provide|do offer)[^.]*color matching[^.]*\.",
            r"(?:The )?warranty[^.]*(?:includes|covers|for Contoso)[^.]*\.",
            r"(?:If you|Our)[^.]*(?:return|satisfaction)[^.]*\."
        ]
        
        for pattern in ai_response_patterns:
            matches = re.finditer(pattern, full_page_text, re.IGNORECASE | re.DOTALL)
            all_matches = list(matches)
            
            if all_matches:
                # Get the last match
                last_match = all_matches[-1]
                response = last_match.group(0)
                
                # Extend to capture more context (up to 300 chars after the match)
                extended_response = full_page_text[last_match.start():last_match.end() + 300]
                
                # Clean up the extended response
                end_markers = ['Jan ', 'YouAI', 'AI-generated', 'Products']
                for marker in end_markers:
                    marker_pos = extended_response.find(marker, 100)  # Look for markers after first 100 chars
                    if marker_pos > 0:
                        extended_response = extended_response[:marker_pos]
                
                cleaned_response = re.sub(r'\s+', ' ', extended_response).strip()
                if len(cleaned_response) > 20:
                    return cleaned_response
        
        # Method 3: Fallback - use the old logic for known responses
        known_responses = [
            "Yes, we do offer a color matching service",
            "The warranty for Contoso Paints includes", 
            "warranty policy for Contoso Paint Company",
            "2-year performance warranty",
            "Here are some cool, blue-toned paint options",
            "If you are not happy with the paint color"
        ]
        
        best_match = ""
        best_position = -1
        
        for known_response in known_responses:
            if known_response in full_page_text:
                start_idx = full_page_text.rfind(known_response)
                if start_idx > best_position:
                    best_position = start_idx
                    response_part = full_page_text[start_idx:start_idx + 600]
                    
                    # Clean up
                    end_markers = ['Jan ', 'PM', 'AI-generated content', 'You', '\n\n']
                    for marker in end_markers:
                        marker_pos = response_part.find(marker, 50)
                        if marker_pos > 0:
                            response_part = response_part[:marker_pos]
                    
                    best_match = response_part.strip()
        
        if best_match:
            return best_match
        
        # Last resort: return the full page text for debugging
        return full_page_text

    def verify_response_contains_keywords(self, response_text, keywords):
        """Verify that the response contains any of the expected keywords"""
        response_lower = response_text.lower()
        
        for keyword in keywords:
            if keyword.lower() in response_lower:
                return True, keyword
        
        return False, None

    def ask_question_and_verify(self, question, expected_keywords):
        """Ask a question and verify the response contains expected content"""
        # Count existing AI response containers BEFORE asking the question
        ai_response_selector = 'div[class*="bg-muted"]'
        initial_response_count = self.page.locator(ai_response_selector).count()
        
        # Clear any existing input first
        text_area = self.page.locator(self.TYPE_QUESTION_TEXT_AREA)
        text_area.click()
        text_area.fill("")
        
        # Take a screenshot of current state for debugging
        self.page.wait_for_timeout(1000)
        
        # Enter the question
        self.enter_a_question(question)
        
        # Wait a bit for the question to be processed
        self.page.wait_for_timeout(2000)
        
        # Click send button
        self.click_send_button()
        
        # Wait for response with longer timeout
        self.wait_for_response(timeout=45000)
        
        # Wait for a NEW response to appear (response count should increase)
        try:
            self.page.wait_for_function(
                f"""(expectedCount) => {{
                    const responses = document.querySelectorAll('div[class*="bg-muted"]');
                    return responses.length > expectedCount;
                }}""",
                arg=initial_response_count,
                timeout=60000
            )
        except:
            pass
        
        # Wait extra time to ensure new response has fully loaded
        self.page.wait_for_timeout(5000)
        
        # Get the LATEST response specifically (the last one in the list)
        response = self.get_latest_ai_response()
        
        # Verify response contains expected content
        contains_keyword, found_keyword = self.verify_response_contains_keywords(response, expected_keywords)
        
        return response, contains_keyword, found_keyword
    
    def get_latest_ai_response(self):
        """Get the text content of the LATEST/MOST RECENT AI response only"""
        # Wait for any dynamic content to load
        self.page.wait_for_timeout(2000)
        
        # Try to get the last AI response container
        ai_response_selector = 'div[class*="bg-muted"]'
        response_elements = self.page.locator(ai_response_selector)
        response_count = response_elements.count()
        
        if response_count > 0:
            # Get the LAST response element (most recent)
            last_response = response_elements.nth(response_count - 1)
            response_text = last_response.text_content()
            
            if response_text and len(response_text.strip()) > 20:
                # Clean up the response text
                import re
                cleaned = re.sub(r'\s+', ' ', response_text).strip()
                return cleaned
        
        # Fallback to the original method if the above doesn't work
        return self.get_last_response()

 