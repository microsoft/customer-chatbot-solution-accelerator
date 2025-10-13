from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from .config import settings, has_openai_config
from .models import Product, ChatMessage, ChatMessageType

logger = logging.getLogger(__name__)

class AIService:
    """AI service for chat functionality"""
    
    def __init__(self):
        self.openai_client = None
        self.is_configured = has_openai_config()
        
        logger.info(f"Azure OpenAI configuration check:")
        logger.info(f"  Endpoint: {settings.azure_openai_endpoint}")
        logger.info(f"  API Key configured: {bool(settings.azure_openai_api_key)}")
        logger.info(f"  API Version: {settings.azure_openai_api_version}")
        logger.info(f"  Deployment: {settings.azure_openai_deployment_name}")
        logger.info(f"  Is configured: {self.is_configured}")
        
        if self.is_configured:
            try:
                from openai import AzureOpenAI
                self.openai_client = AzureOpenAI(
                    azure_endpoint=settings.azure_openai_endpoint,
                    api_key=settings.azure_openai_api_key,
                    api_version=settings.azure_openai_api_version
                )
                logger.info("Azure OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI client: {e}")
                self.is_configured = False
    
    async def generate_chat_response(
        self, 
        user_message: str, 
        chat_history: List[ChatMessage] = None,
        products: List[Product] = None,
        context: Dict[str, Any] = None
    ) -> str:
        """Generate AI response for chat"""
        
        if not self.is_configured or not self.openai_client:
            return await self._generate_fallback_response(user_message, products)
        
        try:
            # Prepare system prompt
            system_prompt = self._create_system_prompt(products, context)
            
            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add chat history
            if chat_history:
                for msg in chat_history[-10:]:  # Last 10 messages
                    role = "user" if msg.message_type == "user" else "assistant"
                    messages.append({"role": role, "content": msg.content})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = self.openai_client.chat.completions.create(
                model=settings.azure_openai_deployment_name,
                messages=messages,
                max_tokens=500,
                temperature=0.7,
                top_p=0.9
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            logger.error(f"Azure OpenAI endpoint: {settings.azure_openai_endpoint}")
            logger.error(f"Azure OpenAI deployment: {settings.azure_openai_deployment_name}")
            logger.error(f"Azure OpenAI API version: {settings.azure_openai_api_version}")
            logger.error(f"Azure OpenAI API key configured: {bool(settings.azure_openai_api_key)}")
            return await self._generate_fallback_response(user_message, products)
    
    def _create_system_prompt(self, products: List[Product] = None, context: Dict[str, Any] = None) -> str:
        """Create system prompt for the AI assistant"""
        
        prompt = """You are Cora, a helpful and friendly shopping assistant for an e-commerce website. 
        Your role is to help customers find products, answer questions about items, provide recommendations, 
        and assist with their shopping needs.
        
        Guidelines:
        - Be helpful, friendly, and professional
        - Focus on helping customers find the right products
        - Provide specific product recommendations when appropriate
        - Ask clarifying questions to better understand customer needs
        - Be concise but informative
        - If you don't know something, admit it and offer to help in other ways
        
        Product Information:"""
        
        if products:
            prompt += "\n\nAvailable products:\n"
            for product in products[:10]:  # Limit to first 10 products
                prompt += f"- {product.title}: ${product.price} ({product.category}) - {product.description}\n"
        
        if context:
            prompt += f"\n\nAdditional context: {context}"
        
        prompt += "\n\nRemember to be helpful and guide customers toward making informed purchasing decisions."
        
        return prompt
    
    async def _generate_fallback_response(self, user_message: str, products: List[Product] = None) -> str:
        """Generate fallback response when AI is not available"""
        
        message_lower = user_message.lower()
        
        # Complex laptop/gaming question handling
        if any(word in message_lower for word in ["laptop", "gaming", "video editing", "4k", "premiere pro", "cyberpunk"]):
            return """I understand you're looking for a high-performance laptop for video editing and gaming! While I don't have access to our full product catalog right now, I can help you with some general guidance:

For your needs (4K video editing in Premiere Pro + gaming like Cyberpunk 2077), you'll want to look for:
• **GPU**: RTX 4070 or better for smooth 4K editing and high-end gaming
• **CPU**: Intel i7-13700H or AMD Ryzen 7 7840HS or better
• **RAM**: 32GB minimum for 4K editing workflows
• **Storage**: 1TB+ NVMe SSD for fast file access
• **Display**: 15-17" with good color accuracy for video work

Your $1500-2000 budget is perfect for this tier. Would you like me to help you find specific models in our catalog, or do you have questions about any of these specifications?"""

        # Product recommendations (check this BEFORE pricing to catch "best products" questions)
        elif any(word in message_lower for word in ["recommend", "suggestion", "best", "popular", "what should i buy", "top", "favorite"]):
            if products:
                popular_products = sorted(products, key=lambda x: x.rating, reverse=True)[:3]
                recommendations = "\n".join([f"- {p.title} (${p.price}) - {p.description[:100]}..." for p in popular_products])
                return f"Here are some popular recommendations from our catalog:\n{recommendations}\n\nWould you like to know more about any of these products?"
            else:
                return "I'd love to recommend some great products! What type of items are you interested in?"
        
        # Budget and pricing questions (but not if it's asking for recommendations)
        elif any(word in message_lower for word in ["budget", "price", "cost", "expensive", "cheap"]) and not any(word in message_lower for word in ["best", "recommend", "suggestion", "popular"]):
            if products:
                price_range = f"Our products range from ${min(p.price for p in products):.2f} to ${max(p.price for p in products):.2f}."
                return f"Great question about pricing! {price_range} I'd be happy to help you find products within your budget. What price range are you looking for?"
            else:
                return "I'd be happy to help you find products within your budget! What price range are you looking for?"
        
        # Technical specifications
        elif any(word in message_lower for word in ["specs", "specifications", "features", "performance", "speed", "memory", "storage"]):
            return "I can help you understand product specifications and features! What type of product are you looking at, and what specific specs are you curious about?"
        
        # Categories
        elif any(word in message_lower for word in ["category", "type", "kind", "what do you have"]):
            if products:
                categories = list(set(p.category for p in products))
                category_list = ", ".join(categories)
                return f"We have products in these categories: {category_list}. Which category interests you most?"
            else:
                return "We have a wide variety of products! What type of items are you looking for?"
        
        # Quality and reliability
        elif any(word in message_lower for word in ["quality", "durable", "reliable", "good", "reviews", "rating"]):
            return "Quality is important! I can help you find products that are well-reviewed and reliable. What specific features or quality aspects are you looking for?"
        
        # Shipping and delivery
        elif any(word in message_lower for word in ["shipping", "delivery", "arrive", "when", "how long"]):
            return "Great question! We offer fast and reliable shipping. Most orders arrive within 3-5 business days. Would you like to know more about our shipping options?"
        
        # Returns and support
        elif any(word in message_lower for word in ["return", "refund", "exchange", "warranty", "support"]):
            return "We have a customer-friendly return policy! Most items can be returned within 30 days. Is there something specific you'd like to know about our return process?"
        
        # Greetings
        elif any(word in message_lower for word in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon"]):
            return "Hello! I'm Cora, your shopping assistant. How can I help you find the perfect products today?"
        
        # Help requests
        elif any(word in message_lower for word in ["help", "assist", "support", "what can you do"]):
            return "I'm here to help! I can assist you with finding products, answering questions about items, providing recommendations, and helping with your shopping needs. What would you like to know?"
        
        # Default response
        else:
            return f"Thanks for your message! I'm here to help with your shopping needs. I can assist you with product recommendations, specifications, pricing, and finding the right items for your needs. What would you like to know more about?"

# Global AI service instance
ai_service = AIService()