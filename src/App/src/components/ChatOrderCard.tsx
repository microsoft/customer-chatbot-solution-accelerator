import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Order } from '@/lib/types';

interface ChatOrderCardProps {
  order: Order;
}

export const ChatOrderCard: React.FC<ChatOrderCardProps> = ({ order }) => {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'delivered': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'shipped': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'processing': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'cancelled': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  return (
    <div className="flex flex-col gap-3 p-4 bg-card border">
      {/* Order Header */}
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-bold text-lg text-foreground">
            Order #{order.orderNumber}
          </h3>
          <p className="text-sm text-muted-foreground">
            {order.orderDate}
          </p>
        </div>
        <Badge className={getStatusColor(order.status)}>
          {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
        </Badge>
      </div>
      
      {/* Order Items */}
      <div className="space-y-2">
        {order.items.map((item, index) => (
          <div key={index} className="flex items-center justify-between p-2 bg-muted/50">
            <div className="flex-1">
              <p className="font-medium text-sm">{item.name}</p>
              <p className="text-xs text-muted-foreground">
                Qty: {item.quantity} × ${item.unitPrice.toFixed(2)}
              </p>
            </div>
            <span className="font-semibold text-sm">
              ${item.totalPrice.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
      
      {/* Order Summary */}
      <div className="border-t pt-3 space-y-1 text-sm">
        <div className="flex justify-between">
          <span>Subtotal:</span>
          <span>${order.subtotal.toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span>Tax:</span>
          <span>${order.tax.toFixed(2)}</span>
        </div>
        <div className="flex justify-between font-bold text-base border-t pt-1">
          <span>Total:</span>
          <span>${order.total.toFixed(2)}</span>
        </div>
      </div>
      
      {/* Shipping Address */}
      <div>
        <h4 className="font-semibold mb-1 text-sm">Shipping Address:</h4>
        <p className="text-sm text-muted-foreground">
          {order.shippingAddress}
        </p>
      </div>
    </div>
  );
};
