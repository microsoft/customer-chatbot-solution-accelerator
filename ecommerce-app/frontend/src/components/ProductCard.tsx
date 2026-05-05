import React from 'react';
import { Link } from 'react-router-dom';
import { Product } from '../types';
import { useAddToCart } from '../hooks/api';
import { useSession } from '../hooks/useSession';
import { ShoppingCartIcon } from '@heroicons/react/24/outline';

interface ProductCardProps {
  product: Product;
  showAddToCart?: boolean;
}

export const ProductCard: React.FC<ProductCardProps> = ({ 
  product, 
  showAddToCart = true 
}) => {
  const { sessionId } = useSession();
  const addToCartMutation = useAddToCart();

  const handleAddToCart = (e: React.MouseEvent) => {
    e.preventDefault(); // Prevent navigation when clicking add to cart
    
    if (!sessionId) return;

    addToCartMutation.mutate({
      sessionId,
      productId: product.id,
      quantity: 1,
    });
  };

  const formatPrice = (price: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-200">
      <Link to={`/products/${product.id}`}>
        <div className="aspect-w-1 aspect-h-1">
          <img
            src={product.image_url}
            alt={product.name}
            className="w-full h-64 object-cover"
            onError={(e) => {
              // Fallback to placeholder if image fails to load
              const target = e.target as HTMLImageElement;
              target.src = `https://via.placeholder.com/400x400/e5e7eb/6b7280?text=${encodeURIComponent(product.name)}`;
            }}
          />
        </div>
      </Link>
      
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <Link to={`/products/${product.id}`}>
              <h3 className="text-lg font-semibold text-gray-900 truncate hover:text-blue-600 transition-colors">
                {product.name}
              </h3>
            </Link>
            
            <p className="text-sm text-gray-500 mt-1 capitalize">
              {product.category}
            </p>
            
            <p className="text-sm text-gray-600 mt-2 line-clamp-2">
              {product.description}
            </p>
          </div>
        </div>
        
        <div className="flex items-center justify-between mt-4">
          <div className="flex flex-col">
            <span className="text-xl font-bold text-gray-900">
              {formatPrice(product.price)}
            </span>
            <span className={`text-xs ${product.in_stock ? 'text-green-600' : 'text-red-600'}`}>
              {product.in_stock 
                ? `${product.stock_quantity} in stock` 
                : 'Out of stock'
              }
            </span>
          </div>
          
          {showAddToCart && product.in_stock && (
            <button
              onClick={handleAddToCart}
              disabled={addToCartMutation.isPending}
              className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
            >
              <ShoppingCartIcon className="h-4 w-4" />
              <span>
                {addToCartMutation.isPending ? 'Adding...' : 'Add to Cart'}
              </span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};