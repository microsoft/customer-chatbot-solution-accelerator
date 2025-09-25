from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosResourceExistsError
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import uuid

from .config import settings
from .models import Product, ProductCreate, ProductUpdate, User, UserCreate, UserUpdate, ChatMessage, ChatMessageCreate, ChatMessageType, ChatSession, ChatSessionCreate, ChatSessionUpdate, Cart, Transaction, TransactionCreate

logger = logging.getLogger(__name__)

class CosmosDatabaseService:
    """Cosmos DB implementation of the database service"""
    
    def __init__(self):
        self.client = CosmosClient(settings.cosmos_db_endpoint, settings.cosmos_db_key)
        self.database = self.client.get_database_client(settings.cosmos_db_database_name)
        self._initialize_containers()
    
    def _serialize_datetime_fields(self, data: dict) -> dict:
        """Convert datetime objects to ISO format for Cosmos DB serialization"""
        serialized_data = data.copy()
        for key, value in serialized_data.items():
            if isinstance(value, datetime):
                serialized_data[key] = value.isoformat()
        return serialized_data
    
    def _deserialize_datetime_fields(self, data: dict) -> dict:
        """Convert ISO string datetime fields back to datetime objects"""
        deserialized_data = data.copy()
        datetime_fields = ['created_at', 'updated_at', 'last_login']
        
        for field in datetime_fields:
            if field in deserialized_data and isinstance(deserialized_data[field], str):
                # Handle both 'Z' suffix and timezone info
                dt_str = deserialized_data[field].replace('Z', '+00:00')
                deserialized_data[field] = datetime.fromisoformat(dt_str)
        
        return deserialized_data
    
    
    def _initialize_containers(self):
        """Initialize Cosmos DB containers"""
        try:
            # Create database if it doesn't exist
            self.database = self.client.create_database_if_not_exists(
                id=settings.cosmos_db_database_name
            )
            
            # Create containers
            self.products_container = self.database.create_container_if_not_exists(
                id=settings.cosmos_db_containers["products"],
                partition_key=PartitionKey(path="/ProductID"),
                offer_throughput=400
            )
            
            self.users_container = self.database.create_container_if_not_exists(
                id=settings.cosmos_db_containers["users"],
                partition_key=PartitionKey(path="/id"),
                offer_throughput=400
            )
            
            self.chat_container = self.database.create_container_if_not_exists(
                id=settings.cosmos_db_containers["chat_sessions"],
                partition_key=PartitionKey(path="/user_id"),
                offer_throughput=400
            )
            
            self.cart_container = self.database.create_container_if_not_exists(
                id=settings.cosmos_db_containers["carts"],
                partition_key=PartitionKey(path="/user_id"),
                offer_throughput=400
            )
            
            self.transactions_container = self.database.create_container_if_not_exists(
                id=settings.cosmos_db_containers["transactions"],
                partition_key=PartitionKey(path="/user_id"),
                offer_throughput=400
            )
            
            logger.info("Cosmos DB containers initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Cosmos DB containers: {str(e)}")
            raise
    
    async def get_products(self, search_params: Dict[str, Any] = None) -> List[Product]:
        """Get products with optional filtering"""
        try:
            query = "SELECT * FROM c"
            parameters = []
            
            if search_params:
                conditions = []
                
                if search_params.get("category") and search_params["category"] != "All":
                    conditions.append("c.category = @category")
                    parameters.append({"name": "@category", "value": search_params["category"]})
                
                if search_params.get("min_price"):
                    conditions.append("c.price >= @min_price")
                    parameters.append({"name": "@min_price", "value": search_params["min_price"]})
                
                if search_params.get("max_price"):
                    conditions.append("c.price <= @max_price")
                    parameters.append({"name": "@max_price", "value": search_params["max_price"]})
                
                if search_params.get("min_rating"):
                    conditions.append("c.rating >= @min_rating")
                    parameters.append({"name": "@min_rating", "value": search_params["min_rating"]})
                
                if search_params.get("in_stock_only"):
                    conditions.append("c.in_stock = true")
                
                if search_params.get("query"):
                    conditions.append("(CONTAINS(LOWER(c.title), LOWER(@query)) OR CONTAINS(LOWER(c.description), LOWER(@query)))")
                    parameters.append({"name": "@query", "value": search_params["query"]})
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            # Add sorting
            sort_by = search_params.get("sort_by", "name") if search_params else "name"
            sort_order = search_params.get("sort_order", "asc") if search_params else "asc"
            
            if sort_by == "name":
                query += f" ORDER BY c.title {'DESC' if sort_order == 'desc' else 'ASC'}"
            elif sort_by == "price":
                query += f" ORDER BY c.price {'DESC' if sort_order == 'desc' else 'ASC'}"
            elif sort_by == "rating":
                query += f" ORDER BY c.rating {'DESC' if sort_order == 'desc' else 'ASC'}"
            
            items = list(self.products_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            # Convert to Product model format
            products = []
            for item in items:
                product = Product(
                    id=item.get("id"),
                    title=item.get("title", ""),
                    price=item.get("price", 0.0),
                    original_price=item.get("original_price", item.get("price", 0.0)),
                    rating=item.get("rating", 4.0),
                    review_count=item.get("review_count", 0),
                    image=item.get("image", ""),
                    category=item.get("category", ""),
                    in_stock=item.get("in_stock", True),
                    description=item.get("description", ""),
                    tags=item.get("tags", []),
                    specifications=item.get("specifications", {})
                )
                products.append(product)
            
            return products
            
        except Exception as e:
            logger.error(f"Error fetching products from Cosmos DB: {str(e)}")
            raise
    
    async def get_product(self, product_id: str) -> Optional[Product]:
        """Get a single product by ID - optimized for Cosmos DB"""
        try:
            # Use direct read for better performance (if we know the partition key)
            # For now, use cross-partition query since products might be in different partitions
            query = "SELECT * FROM c WHERE c.id = @product_id"
            parameters = [{"name": "@product_id", "value": product_id}]
            
            items = list(self.products_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if items:
                item = items[0]
                # Convert datetime strings back to datetime objects
                for field in ['created_at', 'updated_at']:
                    if field in item and isinstance(item[field], str):
                        item[field] = datetime.fromisoformat(item[field].replace('Z', '+00:00'))
                
                # Map Cosmos DB fields to Product model fields
                product = Product(
                    id=item.get("id"),
                    title=item.get("title", ""),
                    price=item.get("price", 0.0),
                    original_price=item.get("original_price", item.get("price", 0.0)),
                    rating=item.get("rating", 4.0),
                    review_count=item.get("review_count", 0),
                    image=item.get("image", ""),
                    category=item.get("category", ""),
                    in_stock=item.get("in_stock", True),
                    description=item.get("description", ""),
                    tags=item.get("tags", []),
                    specifications=item.get("specifications", {}),
                    created_at=item.get("created_at", datetime.utcnow()),
                    updated_at=item.get("updated_at", datetime.utcnow())
                )
                return product
            return None
            
        except Exception as e:
            logger.error(f"Error fetching product from Cosmos DB: {str(e)}")
            raise
    
    async def create_product(self, product: ProductCreate) -> Product:
        """Create a new product"""
        try:
            new_product = Product(
                id=str(uuid.uuid4()),
                **product.dict()
            )
            
            # Serialize datetime fields for Cosmos DB
            product_dict = self._serialize_datetime_fields(new_product.dict())
            self.products_container.create_item(product_dict)
            return new_product
            
        except Exception as e:
            logger.error(f"Error creating product in Cosmos DB: {str(e)}")
            raise
    
    async def update_product(self, product_id: str, product: ProductUpdate) -> Optional[Product]:
        """Update an existing product"""
        try:
            # First get the existing product
            existing_product = await self.get_product(product_id)
            if not existing_product:
                return None
            
            # Update fields
            update_data = product.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(existing_product, field, value)
            
            existing_product.updated_at = datetime.utcnow()
            
            # Replace in Cosmos DB - serialize datetime fields
            product_dict = self._serialize_datetime_fields(existing_product.dict())
            self.products_container.replace_item(
                item=existing_product.id,
                body=product_dict
            )
            
            return existing_product
            
        except Exception as e:
            logger.error(f"Error updating product in Cosmos DB: {str(e)}")
            raise
    
    async def delete_product(self, product_id: str) -> bool:
        """Delete a product"""
        try:
            # First get the product to find its partition key
            product = await self.get_product(product_id)
            if not product:
                return False
            
            # Delete using partition key
            self.products_container.delete_item(
                item=product_id,
                partition_key=product.category
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting product from Cosmos DB: {str(e)}")
            raise
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID - using query for better compatibility"""
        try:
            # Use query instead of direct read to avoid partition_key issues
            query = "SELECT * FROM c WHERE c.id = @user_id"
            parameters = [{"name": "@user_id", "value": user_id}]
            
            items = list(self.users_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if not items:
                return None
            
            user_data = items[0]
            
            # Convert datetime strings back to datetime objects
            for field in ['created_at', 'updated_at', 'last_login']:
                if field in user_data and isinstance(user_data[field], str):
                    user_data[field] = datetime.fromisoformat(user_data[field].replace('Z', '+00:00'))
            
            return User(**user_data)
            
        except CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error fetching user by ID: {str(e)}")
            raise
    
    async def create_user(self, user: UserCreate) -> User:
        """Create a new user"""
        try:
            new_user = User(
                id=str(uuid.uuid4()),
                email=user.email,
                name=user.name
            )
            
            # Convert datetime objects to ISO format for Cosmos DB
            user_dict = self._serialize_datetime_fields(new_user.dict())
            
            self.users_container.create_item(user_dict)
            return new_user
            
        except Exception as e:
            logger.error(f"Error creating user in Cosmos DB: {str(e)}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email - optimized for Cosmos DB"""
        try:
            # Use a simple, efficient query
            query = "SELECT * FROM c WHERE c.email = @email"
            parameters = [{"name": "@email", "value": email}]
            
            # Query across partitions (necessary for email lookup)
            items = list(self.users_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if items:
                # Return the first (and should be only) user found
                user_data = items[0]
                # Convert datetime strings back to datetime objects
                for field in ['created_at', 'updated_at', 'last_login']:
                    if field in user_data and isinstance(user_data[field], str):
                        user_data[field] = datetime.fromisoformat(user_data[field].replace('Z', '+00:00'))
                
                return User(**user_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching user by email: {str(e)}")
            raise
    
    async def create_user_with_password(self, email: str, name: str, password: str) -> User:
        """Create a new user - simplified for Cosmos DB"""
        try:
            new_user = User(
                id=str(uuid.uuid4()),
                email=email,
                name=name
            )
            
            # Convert to dict and serialize datetime fields
            user_dict = new_user.dict()
            for field in ['created_at', 'updated_at', 'last_login']:
                if field in user_dict and isinstance(user_dict[field], datetime):
                    user_dict[field] = user_dict[field].isoformat()
            
            # Create in Cosmos DB using user ID as partition key
            self.users_container.create_item(user_dict)
            return new_user
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    async def update_user(self, user_id: str, user: UserUpdate) -> Optional[User]:
        """Update user - simplified for Cosmos DB"""
        try:
            # Get existing user
            existing_user = await self.get_user(user_id)
            if not existing_user:
                return None
            
            # Update fields
            update_data = user.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(existing_user, field, value)
            
            existing_user.updated_at = datetime.utcnow()
            
            # Convert to dict and serialize datetime fields
            user_dict = existing_user.dict()
            for field in ['created_at', 'updated_at', 'last_login']:
                if field in user_dict and isinstance(user_dict[field], datetime):
                    user_dict[field] = user_dict[field].isoformat()
            
            # Replace in Cosmos DB
            self.users_container.replace_item(
                item=user_id,
                body=user_dict
            )
            
            return existing_user
            
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            raise
    
    # Chat Session Methods
    async def get_chat_session(self, session_id: str, user_id: Optional[str] = None) -> Optional[ChatSession]:
        """Get a chat session by ID"""
        try:
            # Use query to find session by ID
            query = "SELECT * FROM c WHERE c.id = @session_id"
            parameters = [{"name": "@session_id", "value": session_id}]
            
            items = list(self.chat_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if not items:
                return None
            
            session_data = items[0]
            
            # Convert datetime strings back to datetime objects
            for field in ['created_at', 'updated_at', 'last_message_at']:
                if field in session_data and isinstance(session_data[field], str):
                    session_data[field] = datetime.fromisoformat(session_data[field].replace('Z', '+00:00'))
            
            # Convert message datetime fields and ensure message_count is correct
            messages = session_data.get('messages', [])
            for message in messages:
                if 'created_at' in message and isinstance(message['created_at'], str):
                    message['created_at'] = datetime.fromisoformat(message['created_at'].replace('Z', '+00:00'))
            
            # Ensure message_count matches actual message count
            session_data['message_count'] = len(messages)
            
            return ChatSession(**session_data)
            
        except Exception as e:
            logger.error(f"Error fetching chat session from Cosmos DB: {str(e)}")
            raise
    
    async def get_chat_sessions_by_user(self, user_id: str) -> List[ChatSession]:
        """Get all chat sessions for a user"""
        try:
            query = "SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c.last_message_at DESC"
            parameters = [{"name": "@user_id", "value": user_id}]
            
            items = list(self.chat_container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            sessions = []
            for item in items:
                # Convert datetime strings back to datetime objects
                for field in ['created_at', 'updated_at', 'last_message_at']:
                    if field in item and isinstance(item[field], str):
                        item[field] = datetime.fromisoformat(item[field].replace('Z', '+00:00'))
                
                # Convert message datetime fields
                for message in item.get('messages', []):
                    if 'created_at' in message and isinstance(message['created_at'], str):
                        message['created_at'] = datetime.fromisoformat(message['created_at'].replace('Z', '+00:00'))
                
                sessions.append(ChatSession(**item))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error fetching chat sessions from Cosmos DB: {str(e)}")
            raise
    
    async def create_chat_session(self, session: ChatSessionCreate) -> ChatSession:
        """Create a new chat session"""
        try:
            new_session = ChatSession(
                id=str(uuid.uuid4()),
                user_id=session.user_id,
                session_name=session.session_name or f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                context=session.context,
                messages=[],
                message_count=0
            )
            
            # Convert to dict and serialize datetime fields
            session_dict = new_session.dict()
            
            # Serialize datetime fields in the main session
            for field in ['created_at', 'updated_at', 'last_message_at']:
                if field in session_dict and isinstance(session_dict[field], datetime):
                    session_dict[field] = session_dict[field].isoformat()
            
            # Serialize datetime fields in messages
            for msg in session_dict.get('messages', []):
                if 'created_at' in msg and isinstance(msg['created_at'], datetime):
                    msg['created_at'] = msg['created_at'].isoformat()
            
            self.chat_container.create_item(session_dict)
            
            return new_session
            
        except Exception as e:
            logger.error(f"Error creating chat session in Cosmos DB: {str(e)}")
            raise
    
    async def add_message_to_session(self, session_id: str, message: ChatMessageCreate, user_id: Optional[str] = None) -> ChatSession:
        """Add a message to an existing chat session"""
        try:
            # Get existing session
            session = await self.get_chat_session(session_id, user_id)
            if not session:
                # Create new session if it doesn't exist, using the provided session_id
                new_session = ChatSession(
                    id=session_id,  # Use the provided session_id as the actual ID
                    user_id=user_id,
                    session_name=f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                    context={},
                    messages=[],
                    message_count=0
                )
                
                # Convert to dict and serialize datetime fields
                session_dict = new_session.dict()
                
                # Serialize datetime fields in the main session
                for field in ['created_at', 'updated_at', 'last_message_at']:
                    if field in session_dict and isinstance(session_dict[field], datetime):
                        session_dict[field] = session_dict[field].isoformat()
                
                # Serialize datetime fields in messages
                for msg in session_dict.get('messages', []):
                    if 'created_at' in msg and isinstance(msg['created_at'], datetime):
                        msg['created_at'] = msg['created_at'].isoformat()
                
                self.chat_container.create_item(session_dict)
                session = new_session
            
            # Create new message
            new_message = ChatMessage(
                content=message.content,
                message_type=message.message_type or ChatMessageType.USER,
                user_id=user_id,
                metadata=message.metadata
            )
            
            # Add message to session
            session.messages.append(new_message)
            session.message_count = len(session.messages)
            session.last_message_at = new_message.created_at
            session.updated_at = datetime.utcnow()
            
            # Convert session to dict and serialize datetime fields
            session_dict = session.dict()
            
            # Serialize datetime fields in the main session
            for field in ['created_at', 'updated_at', 'last_message_at']:
                if field in session_dict and isinstance(session_dict[field], datetime):
                    session_dict[field] = session_dict[field].isoformat()
            
            # Serialize datetime fields in messages
            for msg in session_dict.get('messages', []):
                if 'created_at' in msg and isinstance(msg['created_at'], datetime):
                    msg['created_at'] = msg['created_at'].isoformat()
            
            # Update session in Cosmos DB
            self.chat_container.upsert_item(session_dict)
            
            # Return the updated session (re-fetch to ensure consistency)
            return await self.get_chat_session(session_id, user_id)
            
        except Exception as e:
            logger.error(f"Error adding message to chat session in Cosmos DB: {str(e)}")
            raise
    
    async def update_chat_session(self, session_id: str, session_update: ChatSessionUpdate, user_id: Optional[str] = None) -> Optional[ChatSession]:
        """Update a chat session"""
        try:
            # Get existing session
            session = await self.get_chat_session(session_id, user_id)
            if not session:
                return None
            
            # Update fields
            update_data = session_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(session, field, value)
            
            session.updated_at = datetime.utcnow()
            
            # Convert to dict and serialize datetime fields
            session_dict = session.dict()
            
            # Serialize datetime fields in the main session
            for field in ['created_at', 'updated_at', 'last_message_at']:
                if field in session_dict and isinstance(session_dict[field], datetime):
                    session_dict[field] = session_dict[field].isoformat()
            
            # Serialize datetime fields in messages
            for msg in session_dict.get('messages', []):
                if 'created_at' in msg and isinstance(msg['created_at'], datetime):
                    msg['created_at'] = msg['created_at'].isoformat()
            
            # Update in Cosmos DB
            self.chat_container.upsert_item(session_dict)
            
            return session
            
        except Exception as e:
            logger.error(f"Error updating chat session in Cosmos DB: {str(e)}")
            raise
    
    async def delete_chat_session(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """Delete a chat session"""
        try:
            # Get session to verify it exists and get partition key
            session = await self.get_chat_session(session_id, user_id)
            if not session:
                return False
            
            # Use the session's user_id or the provided user_id or "anonymous"
            partition_key = session.user_id or user_id or "anonymous"
            
            # Delete session
            self.chat_container.delete_item(
                item=session_id,
                partition_key=partition_key
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting chat session from Cosmos DB: {str(e)}")
            raise
    
    async def get_cart(self, user_id: str) -> Optional[Cart]:
        """Get user's cart - using query for better compatibility"""
        try:
            # Use query instead of direct read to avoid partition_key issues
            query = "SELECT * FROM c WHERE c.user_id = @user_id"
            parameters = [{"name": "@user_id", "value": user_id}]
            
            items = list(self.cart_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if not items:
                return None
            
            cart_data = items[0]
            
            # Convert datetime strings back to datetime objects
            for field in ['created_at', 'updated_at']:
                if field in cart_data and isinstance(cart_data[field], str):
                    cart_data[field] = datetime.fromisoformat(cart_data[field].replace('Z', '+00:00'))
            
            # Convert cart items datetime fields
            for item in cart_data.get('items', []):
                if 'added_at' in item and isinstance(item['added_at'], str):
                    item['added_at'] = datetime.fromisoformat(item['added_at'].replace('Z', '+00:00'))
            
            return Cart(**cart_data)
            
        except Exception as e:
            logger.error(f"Error fetching cart from Cosmos DB: {str(e)}")
            raise
    
    async def update_cart(self, user_id: str, cart: Cart) -> Cart:
        """Update user's cart - optimized for Cosmos DB"""
        try:
            # Set the cart ID to user_id for direct access
            cart.id = user_id
            cart.user_id = user_id
            
            # Convert to dict and serialize datetime fields
            cart_dict = cart.dict()
            for field in ['created_at', 'updated_at']:
                if field in cart_dict and isinstance(cart_dict[field], datetime):
                    cart_dict[field] = cart_dict[field].isoformat()
            
            # Serialize cart items datetime fields
            for item in cart_dict.get('items', []):
                if 'added_at' in item and isinstance(item['added_at'], datetime):
                    item['added_at'] = item['added_at'].isoformat()
            
            # Use upsert for create or update
            self.cart_container.upsert_item(cart_dict)
            
            return cart
            
        except Exception as e:
            logger.error(f"Error updating cart in Cosmos DB: {str(e)}")
            raise
    
    async def create_transaction(self, transaction: TransactionCreate, user_id: str) -> Transaction:
        """Create a new transaction"""
        try:
            new_transaction = Transaction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
                items=transaction.items,
                shipping_address=transaction.shipping_address,
                payment_method=transaction.payment_method,
                payment_reference=transaction.payment_reference
            )
            
            # Calculate totals
            new_transaction.subtotal = sum(item.total_price for item in transaction.items)
            new_transaction.tax = new_transaction.subtotal * 0.08  # 8% tax
            new_transaction.shipping = 9.99 if new_transaction.subtotal < 50 else 0
            new_transaction.total = new_transaction.subtotal + new_transaction.tax + new_transaction.shipping
            
            # Serialize datetime fields for Cosmos DB
            transaction_dict = self._serialize_datetime_fields(new_transaction.dict())
            self.transactions_container.create_item(transaction_dict)
            
            return new_transaction
            
        except Exception as e:
            logger.error(f"Error creating transaction in Cosmos DB: {str(e)}")
            raise

# Global service instance - lazy initialization
cosmos_service = None

def get_cosmos_service():
    """Get the cosmos service instance with lazy initialization"""
    global cosmos_service
    if cosmos_service is None:
        cosmos_service = CosmosDatabaseService()
    return cosmos_service