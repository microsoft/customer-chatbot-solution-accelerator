import asyncio
from app.routers.chat import send_message
from app.models import ChatMessageCreate

async def test_specific_question():
    # Test the exact question you mentioned
    question = 'What are your best products?'
    print(f'Testing: {question}')
    
    message_data = ChatMessageCreate(
        content=question,
        session_id='test-session'
    )
    
    try:
        result = await send_message(message_data)
        print(f'Response: {result["content"]}')
        print(f'Length: {len(result["content"])} chars')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    asyncio.run(test_specific_question())
