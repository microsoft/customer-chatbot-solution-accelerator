## Customer Chatbot Solution Accelerator: Responsible AI FAQ 

- ### What is Customer Chatbot? 

AI GSA Customer Chatbot is designed as an accelerator for building external-facing customer chatbots that leverage generative AI. Its main goal is to enable organizations to quickly deploy chatbots that can answer common customer questions (e.g., purchase, billing, refund, product info) in a personalized, context-aware manner. The solution is built on Azure AI and is intended to be easily customizable and scalable for various business scenarios. 

Users can get quick answers about products, orders, and policies tailored to their specific situation (e.g., order history, preferences). 

 

- ### What can Customer Chatbot do?  

 Fast, Contextual Help: Users can get quick answers about products, orders, and policies tailored to their specific situation (e.g., order history, preferences).  

Personalized Experience: The chatbot adapts its responses based on user profile and previous interactions, making help more relevant and efficient.  

Easy Access: Customers interact with the chatbot directly on the website, without needing special accounts or network access.  

Guided Shopping & Support: The system can recommend products, assist with returns, and provide care instructions, all within a conversational interface.  

 

- ### What is/are Customer Chatbot's intended use(s)? 

Catchers/customers – GBBs/SEs, STU, ATU, IA's 

 

- ### How was Customer Chatbot evaluated? What metrics are used to measure performance? 

user engagement – Impact board metrics: usage, engagement, views, updates etc. 

NOTE: At this time we are not publicly disclosing the Microsoft DSB Process. You can describe the specific assessment activities you performed as part of the DSB process (e.g., red teaming, measurement, mitigations, etc.) but please DO NOT use terms like DSB or Deployment Safety Board in your FAQ.  

 

- ### What are the limitations of Customer Chatbot? How can users minimize the impact of Customer Chatbot's limitations when using the system? 

It's a natural language chat interface to respond to customer queries based on context. The answers are limited to information grounded as sample data 

 

- ### What operational factors and settings allow for effective and responsible use of Customer Chatbot 

We are not using any specific customization or personalized settings on top of default settings for gpt4o mini. We are going through RAI and CELA validation to make sure the system responses are withing the guardrails of compliance. 

 

If your system or product allows for plug ins or extensibility, include the following questions: 

N/A – we are not using additional plugins 

What are plugins and how does Customer Chatbot use them?   

Describe plugins in plain English, including who can develop plugins for this system or product, and what visibility and control the user has over when and how the plugins are used. If appropriate, provide complete plugin descriptions for authorized use, their certification status, and if they have been approved in the marketplace.  

What data can Customer Chatbot provide to plugins? What permissions do Customer Chatbot plugins have?  

Describe user information the plugins can access, store, and transmit to other plugins or 3rd party APIs. List which elements plugins see and what they do not see, e.g., conversation history. Describe what the system does with information provided by the plugin.  

What kinds of issues may arise when using Customer Chatbot enabled with plugins?   

Describe points of failure e.g., incorrect invocation of plugins, fabrications that may occur while sending parameters to plugins, generating results based on plugin responses, etc.   

Describe mechanisms that are available to mitigate errors when the product enabled with plugins causes harm or takes undesired actions, e.g., disabling plugins, reporting issues, etc.   

(Internal reference only) See also the [LASER Generative AI Plugins study](https://microsoft.sharepoint.com/teams/AetherBoard/Shared%20Documents/Forms/AllItems.aspx?id=%2Fteams%2FAetherBoard%2FShared%20Documents%2FGeneral%2FLASER%20Reports%20Final%2Dversion%20storage%2FLaser%20Generative%20AI%20Plugins%20%2D%20report%20%281%29%2Epdf&parent=%2Fteams%2FAetherBoard%2FShared%20Documents%2FGeneral%2FLASER%20Reports%20Final%2Dversion%20storage&p=true&ga=1). 

 